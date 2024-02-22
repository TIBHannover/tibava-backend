from typing import Dict, List

from ..utils.analyser_client import TaskAnalyserClient

from backend.models import PluginRun, PluginRunResult, Video, Timeline
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video

from backend.utils.parser import Parser
from backend.utils.task import Task

from analyser.data import DataManager
from backend.models import (
    Annotation,
    AnnotationCategory,
    PluginRun,
    PluginRunResult,
    TimelineSegmentAnnotation,
    Video,
    TibavaUser,
    Timeline,
    TimelineSegment,
)
from django.db import transaction
from django.conf import settings


@PluginManager.export_parser("whisper")
class WhisperParser(Parser):
    def __init__(self):

        self.valid_parameter = {}


@PluginManager.export_plugin("whisper")
class Whisper(Task):
    def __init__(self):
        self.config = {
            "output_path": "/predictions/",
            "analyser_host": settings.GRPC_HOST,
            "analyser_port": settings.GRPC_PORT,
        }

    def __call__(self, parameters: Dict, video: Video = None, user: TibavaUser = None, plugin_run: PluginRun = None, **kwargs):

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
            "video_to_audio",
            inputs={"video": video_id},
            outputs=["audio"],
        )

        plugin_run.progress = 0.5
        plugin_run.save()

        if result is None:
            raise Exception

        result = self.run_analyser(
            client,
            "whisper",
            inputs={**result[0]},
            downloads=["annotations"],
        )
        if result is None:
            raise Exception
            

        with transaction.atomic():
            with result[1]["annotations"] as data:
                """
                Create a timeline labeled
                """
                annotation_timeline_db = Timeline.objects.create(
                    video=video, name="Whisper Transcript", type=Timeline.TYPE_TRANSCRIPT
                )

                category_db, _ = AnnotationCategory.objects.get_or_create(name="Transcript", video=video, owner=user)


                for annotation in data.annotations:
                    timeline_segment_db = TimelineSegment.objects.create(
                        timeline=annotation_timeline_db,
                        start=annotation.start,
                        end=annotation.end,
                    )
                    for label in annotation.labels:
                        annotation_db, _ = Annotation.objects.get_or_create(
                            name=str(label),
                            video=video,
                            category=category_db,
                            owner=user,
                            # color=color,
                        )

                        TimelineSegmentAnnotation.objects.create(
                            annotation=annotation_db, timeline_segment=timeline_segment_db
                        )

                return {
                    "plugin_run": plugin_run.id.hex,
                    "plugin_run_results": [],
                    "timelines": {"annotations": annotation_timeline_db},
                    "data": {"annotations": result[1]["annotations"].id}
                }