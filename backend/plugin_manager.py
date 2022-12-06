import re
from typing import Dict, Any, List


def convert_name(name):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class Plugin:
    @classmethod
    def __init_subclass__(
        cls,
        config: Dict[str, Any] = None,
        parameters: Dict[str, Any] = None,
        version: str = None,
        **kwargs,
    ):
        super().__init_subclass__(**kwargs)
        cls._default_config = config
        cls._version = version
        cls._parameters = parameters
        cls._name = convert_name(cls.__name__)

    def __init__(self, config=None):
        self._config = self._default_config
        if config is not None:
            self._config.update(config)

    @property
    def config(self):
        return self._config

    @classmethod
    @property
    def default_config(cls):
        return cls._default_config

    @classmethod
    @property
    def version(cls):
        return cls._version

    @classmethod
    @property
    def name(cls):
        return cls._name


class PipelinePlugin:
    def __init__(self):
        pass

    def check_parameters(self, parameters: List[Dict]):
        pass

    def parse_parameters(self, parameters: List[Dict]):
        pass

    def __call__(self):
        pass


class PluginManager:
    _plugins = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def export(cls, name):
        def export_helper(plugin):
            cls._plugins[name] = plugin
            return plugin

        return export_helper

    def __contains__(self, plugin):
        return plugin in self._plugins

    def __call__(self, plugin, parameters=None, **kwargs):
        print(f"[PluginManager] {plugin}: {parameters}", flush=True)
        if plugin not in self._plugins:
            print(f"Plugin: {plugin} not found")

        self._plugins[plugin]()(parameters, **kwargs)

    def get_plugin(self, plugin):
        print(f"[PluginManager::get_plugin] {plugin}", flush=True)
        if plugin not in self._plugins:
            print(f"Plugin: {plugin} not found")

        return self._plugins[plugin]()

    def get_results(self, analyse):
        if not hasattr(analyse, "type"):
            return None
        if analyse.type not in self._plugins:
            return None
        analyser = self._plugins[analyse.type]()
        if not hasattr(analyser, "get_results"):
            return {}
        return analyser.get_results(analyse)
