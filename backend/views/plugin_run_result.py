import os
import shutil
import sys
import json
import uuid
import logging
import traceback
import tempfile
from pathlib import Path

from urllib.parse import urlparse
import imageio

import wand.image as wimage

from backend.utils import download_url, download_file, media_url_to_video

from django.views import View
from django.http import HttpResponse, JsonResponse
from django.conf import settings

# from django.core.exceptions import BadRequest


from backend.models import PluginRunResult, Video, PluginRun
from backend.analyser import Analyser


class PluginRunResultList(View):
    def get(self, request):
        analyser = Analyser()
        try:
            video_id = request.GET.get("video_id")
            if video_id:
                video_db = Video.objects.get(id=video_id)
                analyses = PluginRunResult.objects.filter(plugin_run__video=video_db)
            else:
                analyses = PluginRunResult.objects.all()

            add_results = request.GET.get("add_results", True)
            if add_results:
                entries = []
                for x in analyses:
                    # TODO fix me
                    data = analyser.get_results(x.plugin_run)
                    if data:
                        entries.append({**x.to_dict(), "data": data})
                    else:
                        entries.append({**x.to_dict()})
            else:
                entries = [x.to_dict() for x in analyses]

            return JsonResponse({"status": "ok", "entries": entries})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})