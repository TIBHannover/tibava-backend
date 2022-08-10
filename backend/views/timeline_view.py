import json
import logging
import traceback

from django.views import View
from django.http import JsonResponse


from backend.models import Video, Timeline, TimelineSegment, TimelineView


class TimelineViewList(View):
    def get(self, request):
        try:

            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})
            video_id = request.GET.get("video_id")
            if video_id:
                video_db = Video.objects.get(id=video_id)
                timeline_views = TimelineView.objects.filter(video=video_db)
            else:
                timeline_views = TimelineView.objects.all()

            # TODO
            # timeline_views = timeline_views.select_related("video").select_related("timeline")

            entries = []
            for timeline_view in timeline_views:
                result = timeline_view.to_dict()
                entries.append(result)
            return JsonResponse({"status": "ok", "entries": entries})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class TimelineViewDuplicate(View):
    def post(self, request):
        try:

            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})
            try:
                body = request.body.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
                body = request.body

            try:
                data = json.loads(body)
            except Exception as e:
                return JsonResponse({"status": "error"})
            # get timeline entry to duplicate
            timeline_db = Timeline.objects.get(id=data.get("id"))
            if not timeline_db:
                return JsonResponse({"status": "error"})

            includeannotations = True
            if data.get("includeannotations") is not None and isinstance(data.get("includeannotations"), bool):
                includeannotations = data.get("includeannotations")

            new_timeline_db = timeline_db.clone(includeannotations=includeannotations)

            if data.get("name") and isinstance(data.get("name"), str):
                new_timeline_db.name = data.get("name")
                new_timeline_db.save()

            # create new hash
            return JsonResponse({"status": "ok", "entry": new_timeline_db.to_dict()})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class TimelineViewCreate(View):
    def post(self, request):
        try:

            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})
            try:
                body = request.body.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
                body = request.body

            try:
                data = json.loads(body)
            except Exception as e:
                return JsonResponse({"status": "error"})

            if "video_id" not in data:
                return JsonResponse({"status": "error", "type": "missing_values"})

            create_args = {}
            try:
                video_db = Video.objects.get(id=data.get("video_id"))
                create_args["video"] = video_db
            except Video.DoesNotExist:
                return JsonResponse({"status": "error", "type": "not_exist"})

            if "name" not in data:
                create_args["name"] = "View"
            elif not isinstance(data.get("name"), str):
                return JsonResponse({"status": "error", "type": "wrong_request_body"})
            else:
                create_args["name"] = data.get("name")
            timeline_view_db = TimelineView.objects.create(**create_args)
            # timeline_view_added = [timeline_view_db.to_dict()]

            return JsonResponse({"status": "ok", "entry": timeline_view_db.to_dict()})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class TimelineViewRename(View):
    def post(self, request):
        try:

            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})
            try:
                body = request.body.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
                body = request.body

            try:
                data = json.loads(body)
            except Exception as e:
                return JsonResponse({"status": "error"})

            if "id" not in data:
                return JsonResponse({"status": "error", "type": "missing_values"})
            if "name" not in data:
                return JsonResponse({"status": "error", "type": "missing_values"})
            if not isinstance(data.get("name"), str):
                return JsonResponse({"status": "error", "type": "wrong_request_body"})

            try:
                timeline_db = TimelineView.objects.get(id=data.get("id"))
            except TimelineView.DoesNotExist:
                return JsonResponse({"status": "error", "type": "not_exist"})

            timeline_db.name = data.get("name")
            timeline_db.save()
            return JsonResponse({"status": "ok", "entry": timeline_db.to_dict()})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class TimelineViewDelete(View):
    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})
            try:
                body = request.body.decode("utf-8")
            except (UnicodeDecodeError, AttributeError):
                body = request.body

            try:
                data = json.loads(body)
            except Exception as e:
                return JsonResponse({"status": "error"})
            count, _ = TimelineView.objects.filter(id=data.get("id")).delete()
            if count:
                return JsonResponse({"status": "ok"})
            return JsonResponse({"status": "error"})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})
