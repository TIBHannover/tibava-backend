import os
import sys
import logging
import uuid
import math
import json
from typing import Dict, List

import imageio
import cv2

from celery import shared_task

from backend.models import PluginRun, Video, PluginRunResult
from django.conf import settings
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video
from ..utils.analyser_client import TaskAnalyserClient
from analyser.data import DataManager
from backend.utils.parser import Parser
from backend.utils.task import Task
from django.db import transaction


# @PluginManager.export_parser("thumbnail")
# class ThumbnailParser(Parser):
#     def __init__(self):

#         self.valid_parameter = {
#             "timeline": {"parser": str, "default": "clip"},
#             "search_term": {"parser": str, "required": True},
#             "fps": {"parser": float, "default": 2.0},
#         }


@PluginManager.export_plugin("thumbnail")
class Thumbnail(Task):
    def __init__(self):
        self.config = {
            "fps": 5,
            "max_resolution": 128,
            "output_path": "/predictions/",
            "base_url": "/tibava/thumbnails/",
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
            "thumbnail_generator",
            inputs={"video": video_id},
            downloads=["images"],
        )

        if result is None:
            raise Exception

        # TODO extract all images
        with transaction.atomic():
            with result[1]["images"] as d:
                # extract thumbnails
                d.extract_all(manager)
                plugin_run_result_db = PluginRunResult.objects.create(
                    plugin_run=plugin_run, data_id=d.id, name="images", type=PluginRunResult.TYPE_IMAGES
                )

                return {"plugin_run": plugin_run.id.hex, "plugin_run_results": [plugin_run_result_db.id.hex], "data": {"images": result[1]["images"].id}}


    def get_results(self, analyse):
        try:
            results = json.loads(bytes(analyse.results).decode("utf-8"))
            results = [{**x, "url": self.config.get("base_url") + f"{analyse.id}/{x['path']}"} for x in results]

            return results
        except:
            return []

