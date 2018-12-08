from abc import ABC


class DiscoveredModules(ABC):
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = dict()
        return cls._instance
