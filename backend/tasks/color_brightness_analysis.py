from celery import shared_task

from backend.models import PluginRun, PluginRunResult, Video, Timeline, TimelineSegment
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video

import logging

from .task import TaskAnalyserClient


@PluginManager.export("color_brightness_analysis")
class ColorBrightnessAnalyser:
    def __init__(self):
        self.config = {
            "output_path": "/predictions/",
            "analyser_host": "analyser",
            "analyser_port": 50051,
        }

    def __call__(self, parameters=None, **kwargs):
        video = kwargs.get("video")
        if not parameters:
            parameters = []

        task_parameter = {"timeline": "Color Analysis"}
        for p in parameters:
            if p["name"] in ["timeline"]:
                task_parameter[p["name"]] = str(p["value"])
            elif p["name"] in ["fps"]:
                task_parameter[p["name"]] = int(p["value"])
            else:
                return False

        pluging_run_db = PluginRun.objects.create(
            video=video, type="color_brightness_analysis", status=PluginRun.STATUS_QUEUED
        )

        task = color_brightness_analysis.apply_async(
            (
                {
                    "id": pluging_run_db.id.hex,
                    "video": video.to_dict(),
                    "config": self.config,
                    "parameters": task_parameter,
                },
            )
        )
        return True


@shared_task(bind=True)
def color_brightness_analysis(self, args):

    config = args.get("config")
    parameters = args.get("parameters")
    video = args.get("video")
    id = args.get("id")
    output_path = config.get("output_path")
    analyser_host = config.get("analyser_host", "localhost")
    analyser_port = config.get("analyser_port", 50051)

    print(f"[ColorBrightnessAnalyser] {video}: {parameters}", flush=True)

    video_db = Video.objects.get(id=video.get("id"))
    video_file = media_path_to_video(video.get("id"), video.get("ext"))
    plugin_run_db = PluginRun.objects.get(video=video_db, id=id)

    plugin_run_db.status = PluginRun.STATUS_WAITING
    plugin_run_db.save()

    # print(f"{analyser_host}, {analyser_port}")

    client = TaskAnalyserClient(host=analyser_host, port=analyser_port, plugin_run_db=plugin_run_db)
    data_id = client.upload_file(video_file)
    if data_id is None:
        return
    job_id = client.run_plugin(
        "color_brightness_analyser",
        [{"id": data_id, "name": "video"}],
        [{"name": k, "value": v} for k, v in parameters.items()],
    )
    if job_id is None:
        return
    result = client.get_plugin_results(job_id=job_id, plugin_run_db=plugin_run_db)
    if result is None:
        return

    output_id = None
    for output in result.outputs:
        if output.name == "brightness":
            output_id = output.id

    if output_id is None:
        return
    data = client.download_data(output_id, output_path)

    if data is None:
        return

    plugin_run_result_db = PluginRunResult.objects.create(
        plugin_run=plugin_run_db, data_id=data.id, name="color_brightness_analysis", type=PluginRunResult.TYPE_SCALAR
    )

    _ = Timeline.objects.create(
        video=video_db,
        name=parameters.get("timeline"),
        type=Timeline.TYPE_PLUGIN_RESULT,
        plugin_run_result=plugin_run_result_db,
        visualization=Timeline.VISUALIZATION_SCALAR_LINE,
    )

    plugin_run_db.progress = 1.0
    plugin_run_db.status = PluginRun.STATUS_DONE
    plugin_run_db.save()

    return {"status": "done"}