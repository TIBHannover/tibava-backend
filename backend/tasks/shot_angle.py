import logging
from typing import Dict
from collections import Counter

from backend.models import (
    Annotation,
    PluginRun,
    Video,
    TibavaUser,
    Timeline,
    TimelineSegment,
    TimelineSegmentAnnotation,
)
from backend.plugin_manager import PluginManager

from ..utils.analyser_client import TaskAnalyserClient

from analyser.data import DataManager
from backend.utils.parser import Parser
from backend.utils.task import Task
from django.db import transaction
from django.conf import settings


logger = logging.getLogger(__name__)


@PluginManager.export_parser("shot_angle")
class ShotAngleParser(Parser):
    def __init__(self):
        self.valid_parameter = {
            "timeline": {"parser": str, "default": "Shot Angle"},
        }


@PluginManager.export_plugin("shot_angle")
class ShotAngle(Task):
    def __init__(self):
        self.config = {
            "output_path": "/predictions/",
            "analyser_host": settings.GRPC_HOST,
            "analyser_port": settings.GRPC_PORT,
        }

    def __call__(
        self,
        parameters: Dict,
        video: Video = None,
        user: TibavaUser = None,
        plugin_run: PluginRun = None,
        dry_run: bool = False,
        **kwargs,
    ):
        manager = DataManager(self.config["output_path"])
        client = TaskAnalyserClient(
            host=self.config["analyser_host"],
            port=self.config["analyser_port"],
            plugin_run_db=plugin_run,
            manager=manager,
        )

        video_id = self.upload_video(client, video)
        shot_result = self.run_analyser(
            client,
            "transnet_shotdetection",
            inputs={"video": video_id},
            outputs=["shots"],
        )
        if shot_result is None:
            raise Exception
        shot_angle_result = self.run_analyser(
            client,
            "shot_angle",
            inputs={"video": video_id, "shots": shot_result[0]["shots"]},
            downloads=["annotations"],
        )
        if shot_angle_result is None:
            raise Exception

        if dry_run or plugin_run is None:
            logging.warning("dry_run or plugin_run is None")
            return {}

        color_mapping = {
            "overhead": "#ECF0CC",
            "high": "#D8E299",
            "neutral": "#C5D366",
            "low": "#B1C533",
            "dutch": "#9EB600",
        }

        with transaction.atomic():
            with shot_angle_result[1]["annotations"] as data:
                result_timeline = {}
                timeline = Timeline.objects.create(
                    video=video,
                    name=parameters.get("timeline"),
                    type=Timeline.TYPE_ANNOTATION,
                )
                result_timeline[parameters.get("timeline")] = timeline.id.hex
                for annotation in data.annotations:
                    timeline_segment_db = TimelineSegment.objects.create(
                        timeline=timeline,
                        start=annotation.start,
                        end=annotation.end,
                    )
                    # Show the most predicted label per shot
                    label, count = Counter(annotation.labels).most_common(1)[0]

                    annotation_db, _ = Annotation.objects.get_or_create(
                        name=label,
                        video=video,
                        owner=user,
                        color=color_mapping.get(label, "#EEEEEE"),
                    )

                    TimelineSegmentAnnotation.objects.create(
                        annotation=annotation_db,
                        timeline_segment=timeline_segment_db,
                    )

                return {
                    "plugin_run": plugin_run.id.hex,
                    "plugin_run_results": [],
                    "timelines": result_timeline,
                    "data": {
                        "annotations": shot_angle_result[1]["annotations"].id,
                    },
                }
