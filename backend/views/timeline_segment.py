import os
import shutil
import sys
import json
from typing import Dict
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


from backend.models import AnnotationCategory, Annotation, TimelineSegment, TimelineSegmentAnnotation


class TimelineSegmentAnnotate(View):
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                logging.error("VideoUpload::not_authenticated")
                return JsonResponse({"status": "error"})

            try:
                body = request.body.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
                body = request.body

            try:
                data = json.loads(body)
            except Exception as e:
                return JsonResponse({"status": "error"})

            try:
                segment_db = TimelineSegment.objects.get(hash_id=data.get("timeline_segment_id"))
            except TimelineSegment.DoesNotExist:
                return JsonResponse({"status": "error", "type": "not_exist"})

            # delete all existing annotation for this segment
            TimelineSegmentAnnotation.objects.filter(timeline_segment=segment_db).delete()

            video_db = segment_db.timeline.video
            if "annotations" in data and isinstance(data.get("annotations"), (list, set)):
                for annotation in data.get("annotations"):
                    print("################")
                    print(annotation)
                    # check if there is a category with this name for this video
                    # TODO check name and color in dict
                    annotation_category_db = None
                    if "category" in annotation and isinstance(annotation.get("category"), Dict):
                        category = annotation.get("category")
                        try:
                            annotation_category_db = AnnotationCategory.objects.get(
                                video=video_db, name=category.get("name"), owner=request.user
                            )
                        except AnnotationCategory.DoesNotExist:
                            annotation_category_db = AnnotationCategory.objects.create(
                                name=category.get("name"),
                                color=category.get("color"),
                                video=video_db,
                                owner=request.user,
                            )
                        print(annotation_category_db.to_dict())

                    # check if there is a existing annotation with this name and category for this video
                    # TODO check name and color in dict
                    query_dict = {"video": video_db, "name": annotation.get("name"), "owner": request.user}
                    if annotation_category_db:
                        query_dict["category"] = annotation_category_db
                    else:
                        query_dict["category"] = None
                    try:
                        print(query_dict,flush=True)
                        annotation_db = Annotation.objects.get(**query_dict)
                    except Annotation.DoesNotExist:
                        print({**query_dict, "color": annotation.get("color")})
                        annotation_db = Annotation.objects.create(**{**query_dict, "color": annotation.get("color")})
                    print(annotation_db.to_dict())

                    TimelineSegmentAnnotation.objects.get_or_create(timeline_segment=segment_db, annotation=annotation_db)
            # query_args = {}

            # query_args["timeline__video__owner"] = request.user

            # if "timeline_id" in request.GET:
            #     query_args["timeline__hash_id"] = request.GET.get("timeline_id")

            # if "video_id" in request.GET:
            #     query_args["timeline__video__hash_id"] = request.GET.get("video_id")

            # timeline_segments = TimelineSegment.objects.filter(**query_args)

            # entries = []
            # for segment in timeline_segments:
            #     entries.append(segment.to_dict())
            return JsonResponse({"status": "ok"})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class TimelineSegmentGet(View):
    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})

            query_args = {}

            query_args["timeline__video__owner"] = request.user

            if "timeline_id" in request.GET:
                query_args["timeline__hash_id"] = request.GET.get("timeline_id")

            if "video_id" in request.GET:
                query_args["timeline__video__hash_id"] = request.GET.get("video_id")

            timeline_segments = TimelineSegment.objects.filter(**query_args).order_by("start")

            entries = []
            for segment in timeline_segments:
                entries.append(segment.to_dict())
            return JsonResponse({"status": "ok", "entries": entries})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class TimelineSegmentList(View):
    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})

            query_args = {}

            query_args["timeline__video__owner"] = request.user

            if "timeline_id" in request.GET:
                query_args["timeline__hash_id"] = request.GET.get("timeline_id")

            if "video_id" in request.GET:
                query_args["timeline__video__hash_id"] = request.GET.get("video_id")

            timeline_segments = TimelineSegment.objects.filter(**query_args)

            entries = []
            for segment in timeline_segments:
                entries.append(segment.to_dict())
            return JsonResponse({"status": "ok", "entries": entries})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


# class TimelineSegmentDelete(View):
#     def post(self, request):
#         try:
#             try:
#                 body = request.body.decode("utf-8")
#             except (UnicodeDecodeError, AttributeError):
#                 body = request.body

#             try:
#                 data = json.loads(body)
#             except Exception as e:
#                 return JsonResponse({"status": "error"})
#             count, _ = Timeline.objects.filter(hash_id=data.get("hash_id")).delete()
#             if count:
#                 return JsonResponse({"status": "ok"})
#             return JsonResponse({"status": "error"})
#         except Exception as e:
#             logging.error(traceback.format_exc())
#             return JsonResponse({"status": "error"})
