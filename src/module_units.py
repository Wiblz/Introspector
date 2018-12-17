"""Classes representing module objects."""

import os

from abc import ABC, abstractmethod
from src.util import _get_ast

next_number = -1


class Module(ABC):
    """Abstract base class for modules found in packages and imported in other modules.

    Contains some basic information about modules:
        'number':int unique integer for referencing modules in import chains
        'full_name':str module name preceded by package names separated with '.'. e.g 'package1.package2.module_name'

    """

    @abstractmethod
    def __init__(self, full_name):
        self.number = next_number
        self.full_name = full_name

    def set_number(self):
        global next_number
        next_number += 1
        self.number = next_number

    def purge_number(self):
        self.number = -1


class ModuleUnit(Module):
    """Class representing modules that are found in introspected package or any of it's subpackages"""

    def __init__(self, name, full_name, path):
        super().__init__(full_name)
        self.name = name
        self.path = path
        self.namespace = []
        self.imports = set()
        self.ast = _get_ast(self)
        self._get_namespace()

    def _get_namespace(self):
        from src.visitor import Visitors

        visitor = Visitors.get_instance()
        visitor.set_module(self)
        visitor.visit(self.ast)

    def add_import(self, import_unit):
        """Add imported name to namespace if it is global"""

        if not import_unit.inner:
            self.namespace.append((import_unit.get_ref(), 'imported object'))

        self.imports.add(import_unit)

    def get_imports(self):
        from src.visitor import Visitors

        visitor = Visitors.get_instance(True)
        visitor.set_module(self)
        visitor.visit(self.ast)


class ExternalModule(Module):
    """Class representing modules that are not in introspected package or any of it's subpackages"""

    def __init__(self, full_name):
        super().__init__(full_name)
        index = full_name.rfind('.')
        if index == -1:
            self.name = full_name
        else:
            self.name = full_name[index + 1:]

