from typing import Dict, List
import logging

from ..utils.analyser_client import TaskAnalyserClient

from backend.models import PluginRun, PluginRunResult, Video, Timeline
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video
from backend.utils.parser import Parser
from backend.utils.task import Task
from analyser.data import DataManager
from django.db import transaction


@PluginManager.export_parser("clip")
class CLIPParser(Parser):
    def __init__(self):
        self.valid_parameter = {
            "timeline": {"parser": str, "default": "clip"},
            "search_term": {"parser": str, "required": True},
            "fps": {"parser": float, "default": 2.0},
            "normalize" : {"parser": float, "default": 1},
        }


@PluginManager.export_plugin("clip")
class CLIP(Task):
    def __init__(self):
        self.config = {
            "output_path": "/predictions/",
            "analyser_host": "devbox2.research.tib.eu",
            "analyser_port": 54051,
        }

    def __call__(self, parameters: Dict, video: Video = None, plugin_run: PluginRun = None, **kwargs):
        manager = DataManager(self.config["output_path"])
        client = TaskAnalyserClient(
            host=self.config["analyser_host"],
            port=self.config["analyser_port"],
            plugin_run_db=plugin_run,
            manager=manager,
        )

        video_id = self.upload_video(client, video)
        result = self.run_analyser(
            client,
            "clip_image_embedding",
            parameters={"fps": parameters.get("fps")},
            inputs={"video": video_id},
            outputs=["embeddings"],
        )

        if result is None:
            raise Exception

        result = self.run_analyser(
            client,
            "clip_probs",
            parameters={"search_term": parameters.get("search_term")},
            inputs={**result[0]},
            outputs=["probs"],
        )
        if result is None:
            raise Exception

        result = self.run_analyser(
            client,
            "min_max_norm",
            parameters={"normalize": parameters.get("normalize")},
            inputs={"scalar": result[0]["probs"]},
            downloads=["scalar"],
        )
        if result is None:
            raise Exception

        with transaction.atomic():
            with result[1]["scalar"] as data:
                plugin_run_result_db = PluginRunResult.objects.create(
                    plugin_run=plugin_run, data_id=data.id, name="clip", type=PluginRunResult.TYPE_SCALAR
                )

                timeline_db = Timeline.objects.create(
                    video=video,
                    name=parameters.get("timeline"),
                    type=Timeline.TYPE_PLUGIN_RESULT,
                    plugin_run_result=plugin_run_result_db,
                    visualization=Timeline.VISUALIZATION_SCALAR_COLOR,
                )

                return {
                    "plugin_run": plugin_run.id.hex,
                    "plugin_run_results": [plugin_run_result_db.id.hex],
                    "timelines": {"rms":timeline_db.id.hex},
                    "data": {"rms": result[1]["scalar"].id}
                }