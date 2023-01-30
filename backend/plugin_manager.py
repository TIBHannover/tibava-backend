import logging
import traceback
import sys
from typing import List

from celery import shared_task
from backend.models import PluginRun, Video, User


class PluginManager:
    _plugins = {}
    _parser = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def export_parser(cls, name):
        def export_helper(parser):
            cls._parser[name] = parser
            return parser

        return export_helper

    @classmethod
    def export_plugin(cls, name):
        def export_helper(plugin):
            cls._plugins[name] = plugin
            return plugin

        return export_helper

    def __contains__(self, plugin):
        return plugin in self._plugins

    def __call__(self, plugin: str, parameters: List, video: Video, user: User, run_async: bool = True, **kwargs):
        print(f"########## 4 {parameters}", flush=True)
        print(f"[PluginManager] {plugin}: {parameters}", flush=True)
        if plugin not in self._plugins:
            # TODO
            return False

        print(f"########## 3 {parameters}", flush=True)
        if plugin in self._parser:
            parameters = self._parser[plugin]()(parameters)
        print(f"########## 2 {parameters}", flush=True)

        plugin_run = PluginRun.objects.create(video=video, type=plugin, status=PluginRun.STATUS_QUEUED)
        if run_async:
            run_plugin.apply_async(
                (
                    {
                        "plugin": plugin,
                        "parameters": parameters,
                        "video": video.id,
                        "user": user.id,
                        "plugin_run": plugin_run.id,
                        "kwargs": kwargs,
                    },
                )
            )
        else:
            try:
                self._plugins[plugin]()(parameters, video=video, plugin_run=plugin_run, **kwargs)

            except Exception as e:
                logging.error(f"{plugin} {e}")
                plugin_run.status = PluginRun.STATUS_ERROR
                plugin_run.save()
                return False
        return True

    def get_results(self, analyse):
        if not hasattr(analyse, "type"):
            return None
        if analyse.type not in self._plugins:
            return None
        analyser = self._plugins[analyse.type]()
        if not hasattr(analyser, "get_results"):
            return {}
        return analyser.get_results(analyse)


@shared_task(bind=True)
def run_plugin(self, args):
    plugin = args.get("plugin")
    parameters = args.get("parameters")
    print(f"########## 1 {parameters}", flush=True)
    video = args.get("video")
    user = args.get("user")
    plugin_run = args.get("plugin_run")
    kwargs = args.get("kwargs")

    video_db = Video.objects.get(id=video)
    user_db = User.objects.get(id=user)
    plugin_run_db = PluginRun.objects.get(id=plugin_run)

    plugin_manager = PluginManager()
    try:
        result = plugin_manager._plugins[plugin]()(
            parameters, user=user_db, video=video_db, plugin_run=plugin_run_db, **kwargs
        )
        if result:
            plugin_run_db.progress = 1.0
            plugin_run_db.status = PluginRun.STATUS_DONE
            plugin_run_db.save()
        return

    except Exception as e:
        logging.error(f"{plugin}: {e}")
        exc_type, exc_value, exc_traceback = sys.exc_info()

        traceback.print_exception(
            exc_type,
            exc_value,
            exc_traceback,
            limit=2,
            file=sys.stdout,
        )
    plugin_run_db.status = PluginRun.STATUS_ERROR
    plugin_run_db.save()
