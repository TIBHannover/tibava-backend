import uuid
import logging
import traceback


from django.views import View
from django.http import HttpResponse, JsonResponse
from django.conf import settings

# from django.core.exceptions import BadRequest


from backend.models import Video, PluginRun
from backend.analyser import Analyser


class PluginList(View):
    def get(self, request):
        analyser = Analyser()
        try:
            video_id = request.GET.get("video_id")
            if video_id:
                video_db = Video.objects.get(id=video_id)
                analyses = PluginRun.objects.filter(video=video_db)
            else:
                analyses = PluginRun.objects.all()

            add_results = request.GET.get("add_results")
            if add_results:
                entries = []
                for x in analyses:
                    results = analyser.get_results(x)
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