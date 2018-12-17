from abc import ABC


class DiscoveredModules(ABC):
    """Singleton container for dictionary with 'Module' objects discovered by Introspector"""

    _instance = None

    def __new__(cls, *args, **kwargs):
        raise RuntimeError('%s should not be instantiated. Use "get_instance" instead' % cls)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = dict()
        return cls._instance
