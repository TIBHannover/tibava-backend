from celery import shared_task

from backend.models import PluginRun, PluginRunResult, Video, Timeline
from backend.plugin_manager import PluginManager
from backend.utils import media_path_to_video

from analyser.client import AnalyserClient


@PluginManager.export("insightface_facesize")
class InsightfaceFacesize:
    def __init__(self):
        self.config = {
            "output_path": "/predictions/",
            "analyser_host": "localhost",
            "analyser_port": 50051,
        }

    def __call__(self, video, parameters=None):
        print(f"[InsightfaceFacesize] {video}: {parameters}", flush=True)
        if not parameters:
            parameters = []

        task_parameter = {"timeline": "Face Detection"}
        for p in parameters:
            if p["name"] in "timeline":
                task_parameter[p["name"]] = str(p["value"])
            else:
                return False

        pluging_run_db = PluginRun.objects.create(video=video, type="insightface_facesize", status="Q")

        insightface_detection.apply_async(
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
def insightface_detection(self, args):
    config = args.get("config")
    parameters = args.get("parameters")
    video = args.get("video")
    id = args.get("id")
    output_path = config.get("output_path")
    analyser_host = args.get("analyser_host", "localhost")
    analyser_port = args.get("analyser_port", 50051)

    video_db = Video.objects.get(id=video.get("id"))
    video_file = media_path_to_video(video.get("id"), video.get("ext"))
    plugin_run_db = PluginRun.objects.get(video=video_db, id=id)

    plugin_run_db.status = "R"
    plugin_run_db.save()

    # run insightface_detector
    client = AnalyserClient(analyser_host, analyser_port)
    data_id = client.upload_data(video_file)
    job_id = client.run_plugin("insightface_detector", [{"id": data_id, "name": "video"}], [])
    result = client.get_plugin_results(job_id=job_id)
    if result is None:
        return

    bbox_output_id = None
    for output in result.outputs:
        if output.name == "bboxes":
            bbox_output_id = output.id

    # run insightface_facesize
    job_id = client.run_plugin("insightface_facesize", [{"id": bbox_output_id, "name": "bboxes"}], [])
    result = client.get_plugin_results(job_id=job_id)
    if result is None:
        return

    # get results
    facesize_output_id = None
    for output in result.outputs:
        if output.name == "probs":
            facesize_output_id = output.id

    data = client.download_data(facesize_output_id, output_path)
    # TODO create a timeline labeled by most probable camera setting (per shot)
    # TODO get shot boundaries
    # TODO assign max label to shot boundary
    parent_timeline = Timeline.objects.create(video=video_db, name=parameters.get("timeline"), type="R")

    for index, sub_data in zip(data.index, data.data):
        label_lut = {
            "p_ECU": "Extreme Close-Up",
            "p_CU": "Close-Up",
            "p_MS": "Medium Shot",
            "p_FS": "Full Shot",
            "p_LS": "Long Shot",
        }

        plugin_run_result_db = PluginRunResult.objects.create(
            plugin_run=plugin_run_db,
            data_id=sub_data.id,
            name="insightface_facesizes",
            type="S",  # S stands for SCALAR_DATA
        )
        Timeline.objects.create(
            video=video_db,
            name=label_lut.get(index, index),
            type=Timeline.TYPE_PLUGIN_RESULT,
            plugin_run_result=plugin_run_result_db,
            visualization="SC",
            parent=parent_timeline,
        )

    plugin_run_db.progress = 1.0
    plugin_run_db.status = "D"
    plugin_run_db.save()

    return {"status": "done"}