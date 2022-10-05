import json
import logging
import traceback
import logging

from numpy import isin

import wand.image as wimage


from django.views import View
from django.http import JsonResponse
from django.conf import settings

# from django.core.exceptions import BadRequest


from backend.models import Video, Annotation, AnnotationCategory


def time_to_string(sec, loc="en"):
    sec, sec_frac = divmod(sec, 1)
    min, sec = divmod(sec, 60)
    hours, min = divmod(min, 60)

    sec_frac = round(1000 * sec_frac)
    hours = int(hours)
    min = int(min)
    sec = int(sec)

    if loc == "de":
        return f"{hours}:{min}:{sec},{sec_frac}"
    return f"{hours}:{min}:{sec}.{sec_frac}"


class VideoExportCSV(View):
    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})

            if "video_id" not in request.GET:
                return JsonResponse({"status": "error", "type": "missing_values"})

            try:
                video_db = Video.objects.get(id=request.GET.get("video_id"))
            except Video.DoesNotExist:
                return JsonResponse({"status": "error", "type": "not_exist"})

            annotations = {}
            for annotation in Annotation.objects.filter(video=video_db):
                annotation_dict = annotation.to_dict()
                if annotation.category:
                    annotation_dict["category"] = annotation.category.to_dict()
                annotations[annotation.id] = annotation_dict

            times = []
            durations = []
            timeline_headers = {}
            for timeline_db in video_db.timeline_set.all():
                annotations_headers = {}
                for segment_db in timeline_db.timelinesegment_set.all():
                    times.append(segment_db.start)
                    durations.append(segment_db.end - segment_db.start)
                    for segment_annotation_db in segment_db.timelinesegmentannotation_set.all():
                        annotation_id = segment_annotation_db.annotation.id
                        if annotation_id not in annotations_headers:
                            annotations_headers[annotation_id] = {**annotations[annotation_id], "times": []}
                        annotations_headers[annotation_id]["times"].append(
                            {"start": segment_db.start, "end": segment_db.end}
                        )
                timeline_headers[timeline_db.id] = {"name": timeline_db.name, "annotations": annotations_headers}
            # 0, video_db.duration
            time_duration = sorted(list(set(zip(times, durations))), key=lambda x: x[0])
            # print(time_duration, flush=True)
            # print(len(time_duration), flush=True)
            cols = []

            # first col
            cols.append(["start", "", ""] + [str(t[0]) for t in time_duration])
            cols.append(["start", "", ""] + [time_to_string(t[0], loc="en") for t in time_duration])
            cols.append(["duration", "", ""] + [str(t[1]) for t in time_duration])
            cols.append(["duration", "", ""] + [time_to_string(t[1], loc="en") for t in time_duration])
            for _, timeline in timeline_headers.items():

                for _, annotation in timeline["annotations"].items():
                    col = [timeline["name"]]
                    col.append(annotation["name"])
                    if "category" in annotation:
                        col.append(annotation["category"]["name"])
                    else:
                        col.append("")
                    for t, _ in time_duration:
                        print(t, flush=True)
                        label = 0
                        for anno_t in annotation["times"]:
                            if anno_t["start"] <= t and t < anno_t["end"]:
                                label = 1
                        col.append(str(label))
                        # cols.append([timeline["name"], "", ""] + times)
                    cols.append(col)
            # print(cols, flush=True)
            # Transpose
            rows = list(map(list, zip(*cols)))

            # Back to a single string
            result = "\n".join([",".join(r) for r in rows])

            return JsonResponse({"status": "ok", "file": result})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class VideoExportJson(View):
    def get(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})

            if "video_id" not in request.GET:
                return JsonResponse({"status": "error", "type": "missing_values"})

            try:
                video_db = Video.objects.get(id=request.GET.get("video_id"))
            except Video.DoesNotExist:
                return JsonResponse({"status": "error", "type": "not_exist"})

            annotations = [
                x.to_dict(include_refs_hashes=False, include_refs=True)
                for x in Annotation.objects.filter(video=video_db)
            ]
            timelines = [x.to_dict(include_refs_hashes=False, include_refs=True) for x in video_db.timeline_set.all()]

            result = json.dumps({"annotations": annotations, "timelines": timelines})

            return JsonResponse({"status": "ok", "file": result})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})


class VideoExport(View):
    def export_csv(self, parameters, video_db):

        include_category = True
        if "include_category" in parameters:
            include_category = parameters.get("include_category")

        use_timestamps = True
        if "use_timestamps" in parameters:
            use_timestamps = parameters.get("use_timestamps")

        use_seconds = True
        if "use_seconds" in parameters:
            use_seconds = parameters.get("use_seconds")

        merge_timeline = True
        if "merge_timeline" in parameters:
            merge_timeline = parameters.get("merge_timeline")

        num_header_lines = 1
        if not merge_timeline:
            if include_category:
                num_header_lines = 3
            else:
                num_header_lines = 2

        times = []
        durations = []
        for timeline_db in video_db.timeline_set.all():
            annotations_headers = {}
            for segment_db in timeline_db.timelinesegment_set.all():
                times.append(segment_db.start)
                durations.append(segment_db.end - segment_db.start)
        # 0, video_db.duration
        time_duration = sorted(list(set(zip(times, durations))), key=lambda x: x[0])
        # print(time_duration, flush=True)
        # print(len(time_duration), flush=True)
        cols = []

        # start
        if use_timestamps:
            cols.append(
                ["start"]
                + ["" for x in range(num_header_lines - 1)]
                + [time_to_string(t[0], loc="en") for t in time_duration]
            )
        if use_seconds:
            cols.append(["start"] + ["" for x in range(num_header_lines - 1)] + [str(t[0]) for t in time_duration])

        # duration
        if use_timestamps:
            cols.append(
                ["duration"]
                + ["" for x in range(num_header_lines - 1)]
                + [time_to_string(t[1], loc="en") for t in time_duration]
            )
        if use_seconds:
            cols.append(["duration"] + ["" for x in range(num_header_lines - 1)] + [str(t[1]) for t in time_duration])

        annotations = {}
        for annotation in Annotation.objects.filter(video=video_db):
            annotation_dict = annotation.to_dict()
            if annotation.category:
                annotation_dict["category"] = annotation.category.to_dict()
            annotations[annotation.id] = annotation_dict

        if merge_timeline:
            for timeline_db in video_db.timeline_set.all():
                segments = []
                for segment_db in timeline_db.timelinesegment_set.all():
                    annotations = []
                    for segment_annotation_db in segment_db.timelinesegmentannotation_set.all():
                        if include_category and segment_annotation_db.annotation.category:
                            annotations.append(
                                segment_annotation_db.annotation.category.name
                                + "::"
                                + segment_annotation_db.annotation.name
                            )
                        else:
                            annotations.append(segment_annotation_db.annotation.name)
                    if len(annotations) > 0:
                        segments.append(
                            {"annotation": "+".join(annotations), "start": segment_db.start, "end": segment_db.end}
                        )

                if len(segments) == 0:
                    continue

                col = [timeline_db.name]

                for s, d in time_duration:
                    col_text = ""

                    for segment in segments:
                        if segment["start"] >= s and segment["end"] <= (s + d):
                            col_text = segment["annotation"]

                    col.append(col_text)

                cols.append(col)

        else:
            timeline_headers = {}
            for timeline_db in video_db.timeline_set.all():
                annotations_headers = {}
                for segment_db in timeline_db.timelinesegment_set.all():
                    for segment_annotation_db in segment_db.timelinesegmentannotation_set.all():
                        annotation_id = segment_annotation_db.annotation.id
                        if annotation_id not in annotations_headers:
                            annotations_headers[annotation_id] = {**annotations[annotation_id], "times": []}
                        annotations_headers[annotation_id]["times"].append(
                            {"start": segment_db.start, "end": segment_db.end}
                        )
                timeline_headers[timeline_db.id] = {"name": timeline_db.name, "annotations": annotations_headers}

            for _, timeline in timeline_headers.items():

                for _, annotation in timeline["annotations"].items():
                    col = [timeline["name"]]
                    col.append(annotation["name"])
                    if include_category:
                        if "category" in annotation:
                            col.append(annotation["category"]["name"])
                        else:
                            col.append("")
                    for t, _ in time_duration:
                        print(t, flush=True)
                        label = 0
                        for anno_t in annotation["times"]:
                            if anno_t["start"] <= t and t < anno_t["end"]:
                                label = 1
                        col.append(str(label))
                        # cols.append([timeline["name"], "", ""] + times)
                    cols.append(col)
        # print(cols, flush=True)
        # Transpose
        rows = list(map(list, zip(*cols)))

        # Back to a single string
        result = "\n".join([",".join(r) for r in rows])

        return result

    def post(self, request):
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error"})

            if "video_id" not in request.POST:
                return JsonResponse({"status": "error", "type": "missing_values"})

            try:
                video_db = Video.objects.get(id=request.POST.get("video_id"))
            except Video.DoesNotExist:
                return JsonResponse({"status": "error", "type": "not_exist"})

            if "format" not in request.POST:
                return JsonResponse({"status": "error", "type": "missing_values"})

            parameters = {}
            if "parameters" in request.POST:
                if isinstance(request.POST.get("parameters"), str):
                    try:
                        input_parameters = json.loads(request.POST.get("parameters"))
                    except:
                        return JsonResponse({"status": "error", "type": "wrong_request_body"})
                elif isinstance(request.POST.get("parameters"), (list, set)):
                    input_parameters = request.POST.get("parameters")
                else:
                    return JsonResponse({"status": "error", "type": "wrong_request_body"})

                for p in input_parameters:
                    if "name" not in p:
                        return JsonResponse({"status": "error", "type": "missing_values"})
                    if "value" not in p:
                        return JsonResponse({"status": "error", "type": "missing_values"})
                    parameters[p["name"]] = p["value"]

            if request.POST.get("format") == "csv":
                result = self.export_csv(parameters, video_db)
                return JsonResponse({"status": "ok", "file": result, "extension": "csv"})

            return JsonResponse({"status": "error", "type": "unknown_format"})
        except Exception as e:
            logging.error(traceback.format_exc())
            return JsonResponse({"status": "error"})
