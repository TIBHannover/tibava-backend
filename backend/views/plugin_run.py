import os
import re
import shutil
import sys
import json
import uuid
import logging
import traceback
import tempfile
from pathlib import Path
import tempfile

from urllib.parse import urlparse
import imageio

import wand.image as wimage

from backend.utils import download_url, download_file, media_url_to_video

from django.views import View
from django.http import HttpResponse, JsonResponse
from django.conf import settings

# from django.core.exceptions import BadRequest


from backend.models import Video, PluginRun
from backend.plugin_manager import PluginManager


class PluginRunNew(View):
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                logging.error("PluginRunNew::not_authenticated")
                return JsonResponse({"status": "error"})

            if request.method != "POST":
                logging.error("PluginRunNew::wrong_method")
                return JsonResponse({"status": "error"})

            output_dir = tempfile.mkdtemp()
            parameters = []

            for k, v in request.FILES.items():
                m = re.match(r"^file_(.*?)$", k)
                if m:
                    data_id_uuid = uuid.uuid4().hex
                    download_result = download_file(
                        output_dir=output_dir,
                        output_name=data_id_uuid,
                        file=v,
                        max_size=11 * 1024 * 1024 * 1024,
                    )

                    if download_result.get("status") == "ok":
                        parameters.append(
                            {
                                "name": m.group(1),
                                "value": download_result.get("origin"),
                                "path": download_result.get("path"),
                            }
                        )
            parameters.extend(json.loads(request.POST.get("parameters")))
            plugin = request.POST.get("plugin")
            if plugin is None:
                return JsonResponse({"status": "error", "type": "missing_values"})

            video_id = request.POST.get("video_id")
            if video_id is None:
                return JsonResponse({"status": "error", "type": "missing_values"})

            if not isinstance(parameters, list):
                return JsonResponse({"status": "error", "type": "wrong_request_body"})
            valid_parameters = []
            for parameter in parameters:
                if not isinstance(parameter, dict):
                    return JsonResponse({"status": "error", "type": "wrong_request_body"})

                if "name" not in parameter:
                    return JsonResponse({"status": "error", "type": "wrong_request_body"})

                if "value" not in parameter:
                    return JsonResponse({"status": "error", "type": "wrong_request_body"})
                if "path" in parameter:
                    valid_parameters.append(
                        {"name": parameter.get("name"), "value": parameter.get("value"), "path": parameter.get("path")}
                    )

                else:
                    valid_parameters.append({"name": parameter.get("name"), "value": parameter.get("value")})

            plugin_manager = PluginManager()
            if plugin not in plugin_manager:
                return JsonResponse({"status": "error", "type": "not_exist"})

            try:
                video_db = Video.objects.get(id=video_id)
            except Video.DoesNotExist:
                return JsonResponse({"status": "error", "type": "not_exist"})

            user_db = request.user

            result = plugin_manager(plugin, user=user_db, video=video_db, parameters=valid_parameters)

            if result:
                return JsonResponse({"status": "ok"})
            return JsonResponse({"status": "error", "type": "plugin_not_started"})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class PluginRunList(View):
    def get(self, request):
        if not request.user.is_authenticated:
            logging.error("PluginRunNew::not_authenticated")
            return JsonResponse({"status": "error"})

        plugin_manager = PluginManager()
        try:
            video_id = request.GET.get("video_id")
            if video_id:
                analyses = PluginRun.objects.filter(video__id=video_id, video__owner=request.user)
            else:
                analyses = PluginRun.objects.filter(video__owner=request.user)
            # print(len(analyses), flush=True)
            add_results = request.GET.get("add_results")
            if add_results:
                entries = []
                for x in analyses:
                    results = plugin_manager.get_results(x)
                    if results:
                        entries.append({**x.to_dict(), "results": results})
                    else:
                        entries.append({**x.to_dict()})
            else:
                entries = [x.to_dict() for x in analyses]

            return JsonResponse({"status": "ok", "entries": entries})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})
