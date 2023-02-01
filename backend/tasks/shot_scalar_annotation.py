import random
from typing import Dict, List


from backend.utils import rgb_to_hex, hsv_to_rgb

from ..utils.analyser_client import TaskAnalyserClient

from analyser.data import Shot, ShotsData

from backend.models import (
    Annotation,
    AnnotationCategory,
    PluginRun,
    PluginRunResult,
    TimelineSegmentAnnotation,
    Video,
    User,
    Timeline,
    TimelineSegment,
)
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video

from analyser.data import DataManager
from backend.utils.parser import Parser
from backend.utils.task import Task

PLUGIN_NAME = "ShotScalarAnnotation"


@PluginManager.export_parser("shot_scalar_annotation")
class ShotScalarAnnotationParser(Parser):
    def __init__(self):

        self.valid_parameter = {
            "timeline": {"parser": str, "default": "Face Emotion"},
            "shot_timeline_id": {"required": True},
            "scalar_timeline_id": {"required": True},
        }


@PluginManager.export_plugin("shot_scalar_annotation")
class ShotScalarAnnotation(Task):
    def __init__(self):
        self.config = {
            "output_path": "/predictions/",
            "analyser_host": "analyser",
            "analyser_port": 50051,
        }

    def __call__(
        self, parameters: Dict, video: Video = None, user: User = None, plugin_run: PluginRun = None, **kwargs
    ):
        manager = DataManager(self.config["output_path"])
        client = TaskAnalyserClient(
            host=self.config["analyser_host"],
            port=self.config["analyser_port"],
            plugin_run_db=plugin_run,
            manager=manager,
        )

        shot_timeline_db = Timeline.objects.get(id=parameters.get("shot_timeline_id"))
        if shot_timeline_db.type != Timeline.TYPE_ANNOTATION:
            raise Exception

        shots = manager.create_data("ShotsData")
        with shots:

            shot_timeline_segments = TimelineSegment.objects.filter(timeline=shot_timeline_db)
            for x in shot_timeline_segments:
                shots.shots.append(Shot(start=x.start, end=x.end))
        shots_id = client.upload_data(shots)

        scalar_timeline_db = Timeline.objects.get(id=parameters.get("scalar_timeline_id"))
        if scalar_timeline_db.type != Timeline.TYPE_PLUGIN_RESULT:
            raise Exception
        if scalar_timeline_db.plugin_run_result.type != PluginRunResult.TYPE_SCALAR:
            raise Exception

        print(f"++++++++++++++++++ {scalar_timeline_db.plugin_run_result.data_id}", flush=True)
        scalar_data = manager.load(scalar_timeline_db.plugin_run_result.data_id)
        if scalar_data is None:
            raise Exception

        print(f"++++++++++++++++++ {scalar_data}", flush=True)
        scalar_id = client.upload_data(scalar_data)

        result = self.run_analyser(
            client,
            "shot_scalar_annotator",
            inputs={"shots": shots_id, "scalar": scalar_id},
            downloads=["annotations"],
        )

        if result is None:
            raise Exception

        with result[1]["annotations"] as data:
            """
            Create a timeline labeled
            """
            print(f"[{PLUGIN_NAME}] Create annotation timeline", flush=True)
            annotation_timeline = Timeline.objects.create(
                video=video, name=parameters.get("timeline"), type=Timeline.TYPE_ANNOTATION
            )

            category_db, _ = AnnotationCategory.objects.get_or_create(name="value", video=video, owner=user)

            values = []
            for annotation in data.annotations:
                for label in annotation.labels:
                    try:
                        values.append(float(label))
                    except:
                        continue
            min_val = min(values)
            max_val = max(values)

            h = random.random() * 359 / 360
            s = 0.6

            for annotation in data.annotations:
                timeline_segment_db = TimelineSegment.objects.create(
                    timeline=annotation_timeline,
                    start=annotation.start,
                    end=annotation.end,
                )
                for label in annotation.labels:
                    value = label
                    try:
                        v = (float(label) - min_val) / (max_val - min_val)
                        value = round(float(label), 3)
                    except:
                        v = 0.6
                    color = rgb_to_hex(hsv_to_rgb(h, s, v))
                    annotation_db, _ = Annotation.objects.get_or_create(
                        name=str(value),
                        video=video,
                        category=category_db,
                        owner=user,
                        color=color,
                    )

                    TimelineSegmentAnnotation.objects.create(
                        annotation=annotation_db, timeline_segment=timeline_segment_db
                    )
