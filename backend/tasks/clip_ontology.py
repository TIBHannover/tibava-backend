from typing import Dict, List
import logging
import csv

from ..utils.analyser_client import TaskAnalyserClient

from backend.models import (
    PluginRun,
    PluginRunResult,
    Video,
    Timeline,
    TimelineSegment,
    AnnotationCategory,
    Annotation,
    TimelineSegmentAnnotation,
    User,
)
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video
from backend.utils.parser import Parser
from backend.utils.task import Task
from analyser.data import Shot, DataManager


@PluginManager.export_parser("clip_ontology")
class CLIPParser(Parser):
    def __init__(self):
        self.valid_parameter = {
            "timeline": {"parser": str, "default": "clip"},
            "shot_timeline_id": {"default": None},
            "concept_csv": {"parser": str, "required": True},
            "fps": {"parser": float, "default": 2.0},
        }


@PluginManager.export_plugin("clip_ontology")
class CLIPOntology(Task):
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
        concept_csv_path = parameters.get("concept_csv")
        print(concept_csv_path, flush=True)
        concepts = []
        with open(concept_csv_path) as f:
            reader = csv.reader(f)
            for line in reader:
                concepts.append({"timeline": line[0], "search_term": line[1]})
        print(concepts, flush=True)
        # return

        concepts_data = manager.create_data("ListData")
        with concepts_data as d:
            for concept in concepts:
                with d.create_data("StringData", concept["timeline"]) as concept_data:
                    concept_data.text = concept["search_term"]
        concepts_id = client.upload_data(concepts_data)
        print(concepts_id, flush=True)

        shots_id = None
        if parameters.get("shot_timeline_id"):
            shot_timeline_db = Timeline.objects.get(id=parameters.get("shot_timeline_id"))
            shot_timeline_segments = TimelineSegment.objects.filter(timeline=shot_timeline_db)

            shots = manager.create_data("ShotsData")
            with shots:
                for x in shot_timeline_segments:
                    shots.shots.append(Shot(start=x.start, end=x.end))
            shots_id = client.upload_data(shots)

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
            "clip_ontology_probs",
            parameters={},
            inputs={**result[0], "concepts": concepts_id},
            outputs=["probs"],
        )
        if result is None:
            raise Exception

        aggregate_result = self.run_analyser(
            client,
            "aggregate_list_scalar_per_time",
            inputs={"scalars": result[0]["probs"]},
            downloads=["aggregated_scalars"],
        )
        if aggregate_result is None:
            raise Exception

        with aggregate_result[1]["aggregated_scalars"] as data:
            # Annotate shots
            if shots_id:
                annotater_result = self.run_analyser(
                    client,
                    "shot_annotator",
                    inputs={"shots": shots_id, "probs": data.id},
                    downloads=["annotations"],
                )

                if annotater_result is None:
                    raise Exception
                with annotater_result[1]["annotations"] as annotations_data:
                    annotation_timeline = Timeline.objects.create(
                        video=video, name=parameters.get("timeline"), type=Timeline.TYPE_ANNOTATION
                    )

                    category_db, _ = AnnotationCategory.objects.get_or_create(name="Emotion", video=video, owner=user)

                    for annotation in annotations_data.annotations:
                        # create TimelineSegment
                        timeline_segment_db = TimelineSegment.objects.create(
                            timeline=annotation_timeline,
                            start=annotation.start,
                            end=annotation.end,
                        )

                        for label in annotation.labels:
                            # add annotion to TimelineSegment
                            annotation_db, _ = Annotation.objects.get_or_create(
                                name=label, video=video, category=category_db, owner=user
                            )

                            TimelineSegmentAnnotation.objects.create(
                                annotation=annotation_db, timeline_segment=timeline_segment_db
                            )

            data.extract_all(manager)
            for index, sub_data in zip(data.index, data.data):
                plugin_run_result_db = PluginRunResult.objects.create(
                    plugin_run=plugin_run,
                    data_id=sub_data,
                    name="face_emotion",
                    type=PluginRunResult.TYPE_SCALAR,
                )
                Timeline.objects.create(
                    video=video,
                    name=index,
                    type=Timeline.TYPE_PLUGIN_RESULT,
                    plugin_run_result=plugin_run_result_db,
                    visualization=Timeline.VISUALIZATION_SCALAR_COLOR,
                    parent=annotation_timeline,
                )
        # result = self.run_analyser(
        #     client,
        #     "min_max_norm",
        #     inputs={"scalar": result[0]["probs"]},
        #     downloads=["scalar"],
        # )
        # if result is None:
        #     raise Exception

        # with result[1]["scalar"] as data:
        #     plugin_run_result_db = PluginRunResult.objects.create(
        #         plugin_run=plugin_run, data_id=data.id, name="clip", type=PluginRunResult.TYPE_SCALAR
        #     )

        #     _ = Timeline.objects.create(
        #         video=video,
        #         name=parameters.get("timeline"),
        #         type=Timeline.TYPE_PLUGIN_RESULT,
        #         plugin_run_result=plugin_run_result_db,
        #         visualization=Timeline.VISUALIZATION_SCALAR_COLOR,
        #     )
