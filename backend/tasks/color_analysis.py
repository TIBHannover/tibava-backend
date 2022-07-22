from celery import shared_task

from backend.models import PluginRun, PluginRunResult, Video, Timeline, TimelineSegment
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video

import logging

from analyser.client import AnalyserClient


@PluginManager.export("color_analysis")
class ColorAnalyser:
    def __init__(self):
        self.config = {
            "output_path": "/predictions/",
            "analyser_host": "localhost",
            "analyser_port": 50051,
        }

    def __call__(self, parameters=None, **kwargs):
        video = kwargs.get("video")
        if not parameters:
            parameters = []

        task_parameter = {"timeline": "Color Analysis", "k": 4, "timeline_visualization": 0}
        for p in parameters:
            if p["name"] in ["timeline"]:
                task_parameter[p["name"]] = str(p["value"])
            elif p["name"] in ["k", "fps", "max_resolution", "max_iter"]:
                task_parameter[p["name"]] = int(p["value"])
            else:
                return False

        pluging_run_db = PluginRun.objects.create(video=video, type="color_analysis", status="Q")

        task = color_analysis.apply_async(
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
def color_analysis(self, args):

    config = args.get("config")
    parameters = args.get("parameters")
    video = args.get("video")
    id = args.get("id")
    output_path = config.get("output_path")
    analyser_host = config.get("analyser_host", "localhost")
    analyser_port = config.get("analyser_port", 50051)

    print(f"[ColorAnalyser] {video}: {parameters}", flush=True)

    video_db = Video.objects.get(id=video.get("id"))
    video_file = media_path_to_video(video.get("id"), video.get("ext"))
    plugin_run_db = PluginRun.objects.get(video=video_db, id=id)

    plugin_run_db.status = "R"
    plugin_run_db.save()

    # print(f"{analyser_host}, {analyser_port}")

    client = AnalyserClient(analyser_host, analyser_port)
    data_id = client.upload_file(video_file)
    job_id = client.run_plugin(
        "color_analyser",
        [{"id": data_id, "name": "video"}],
        [{"name": k, "value": v} for k, v in parameters.items()],
    )
    result = client.get_plugin_results(job_id=job_id)
    if result is None:
        return

    output_id = None
    for output in result.outputs:
        if output.name == "colors":
            output_id = output.id

    data = client.download_data(output_id, output_path)

    parent_timeline = None
    if len(data.data) > 1:
        parent_timeline = Timeline.objects.create(
            video=video_db,
            name=parameters.get("timeline"),
            type="R",
        )

    for i, d in enumerate(data.data):
        plugin_run_result_db = PluginRunResult.objects.create(
            plugin_run=plugin_run_db, data_id=d.id, name="color_analysis", type="R"  # R stands for RGB_HIST_DATA
        )

        _ = Timeline.objects.create(
            video=video_db,
            name=parameters.get("timeline") + f" #{i}" if len(data.data) > 1 else parameters.get("timeline"),
            type=Timeline.TYPE_PLUGIN_RESULT,
            plugin_run_result=plugin_run_result_db,
            visualization="C",
            parent=parent_timeline,
        )

    plugin_run_db.progress = 1.0
    plugin_run_db.status = "D"
    plugin_run_db.save()

    return {"status": "done"}
