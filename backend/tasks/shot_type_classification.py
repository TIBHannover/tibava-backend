from typing import Dict, List

from celery import shared_task

from backend.models import (
    Annotation,
    AnnotationCategory,
    PluginRun,
    PluginRunResult,
    Video,
    TibavaUser,
    Timeline,
    TimelineSegment,
    TimelineSegmentAnnotation,
)
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video

from ..utils.analyser_client import TaskAnalyserClient
from analyser.data import Shot, ShotsData

from analyser.data import DataManager
from backend.utils.parser import Parser
from backend.utils.task import Task


LABEL_LUT = {
    "p_ECU": "Extreme Close-Up",
    "p_CU": "Close-Up",
    "p_MS": "Medium Shot",
    "p_FS": "Full Shot",
    "p_LS": "Long Shot",
}
PLUGIN_NAME = "ShotTypeClassifier"


@PluginManager.export_parser("shot_type_classification")
class ShotTypeClassifierParser(Parser):
    def __init__(self):

        self.valid_parameter = {
            "timeline": {"parser": str, "default": "Camera Setting"},
            "fps": {"parser": float, "default": 2.0},
            "shot_timeline_id": {},
        }


@PluginManager.export_plugin("shot_type_classification")
class ShotTypeClassifier(Task):
    def __init__(self):
        self.config = {
            "output_path": "/predictions/",
            "analyser_host": "analyser",
            "analyser_port": 50051,
        }

    def __call__(
        self, parameters: Dict, video: Video = None, user: TibavaUser = None, plugin_run: PluginRun = None, **kwargs
    ):
        # Debug
        parameters["fps"] = 0.1
        manager = DataManager(self.config["output_path"])
        client = TaskAnalyserClient(
            host=self.config["analyser_host"],
            port=self.config["analyser_port"],
            plugin_run_db=plugin_run,
            manager=manager,
        )

        video_id = self.upload_video(client, video)

        shots_id = None
        if parameters.get("shot_timeline_id"):
            shot_timeline_db = Timeline.objects.get(id=parameters.get("shot_timeline_id"))
            shot_timeline_segments = TimelineSegment.objects.filter(timeline=shot_timeline_db)

            shots = manager.create_data("ShotsData")
            with shots:
                for x in shot_timeline_segments:
                    shots.shots.append(Shot(start=x.start, end=x.end))
            shots_id = client.upload_data(shots)

        result = self.run_analyser(
            client,
            "shot_type_classifier",
            inputs={"video": video_id},
            outputs=["probs"],
            downloads=["probs"],
        )

        if result is None:
            raise Exception

        if shots_id:

            annotations_result = self.run_analyser(
                client,
                "shot_annotator",
                inputs={"probs": result[0]["probs"], "shots": shots_id},
                downloads=["annotations"],
            )
            if annotations_result is None:
                raise Exception

            """
            Create a timeline labeled by most probable class (per shot)
            """
            print(f"[{PLUGIN_NAME}] Create annotation timeline", flush=True)
            annotation_timeline = Timeline.objects.create(
                video=video, name=parameters.get("timeline"), type=Timeline.TYPE_ANNOTATION
            )

            category_db, _ = AnnotationCategory.objects.get_or_create(name="Shot Size", video=video, owner=user)

            with annotations_result[1]["annotations"] as annotations:
                for annotation in annotations.annotations:
                    # create TimelineSegment
                    timeline_segment_db = TimelineSegment.objects.create(
                        timeline=annotation_timeline,
                        start=annotation.start,
                        end=annotation.end,
                    )

                    for label in annotation.labels:
                        # add annotion to TimelineSegment
                        annotation_db, _ = Annotation.objects.get_or_create(
                            name=LABEL_LUT.get(label, label), video=video, category=category_db, owner=user
                        )

                        TimelineSegmentAnnotation.objects.create(
                            annotation=annotation_db, timeline_segment=timeline_segment_db
                        )

        """
        Create timeline(s) with probability of each class as scalar data
        """
        print(f"[{PLUGIN_NAME}] Create scalar color (SC) timeline with probabilities for each class", flush=True)

        with result[1]["probs"] as data:

            data.extract_all(manager)
            for index, sub_data in zip(data.index, data.data):

                plugin_run_result_db = PluginRunResult.objects.create(
                    plugin_run=plugin_run,
                    data_id=sub_data,
                    name="shot_type_classification",
                    type=PluginRunResult.TYPE_SCALAR,
                )
                Timeline.objects.create(
                    video=video,
                    name=LABEL_LUT.get(index, index),
                    type=Timeline.TYPE_PLUGIN_RESULT,
                    plugin_run_result=plugin_run_result_db,
                    visualization=Timeline.VISUALIZATION_SCALAR_COLOR,
                    parent=annotation_timeline,
                )
