import ast
from abc import ABC

import _ast

from src.DiscoveredModules import DiscoveredModules
from src.importUnit import ImportUnit
import src.importUnit as importUnit


class Visitors(ABC):
    _import_visitor_instance = None
    _member_visitor_instance = None

    @classmethod
    def get_instance(cls, import_visitor=False):
        if import_visitor:
            if cls._import_visitor_instance is None:
                cls._import_visitor_instance = _ImportVisitor()
            return cls._import_visitor_instance
        else:
            if cls._member_visitor_instance is None:
                cls._member_visitor_instance = _MemberVisitor()
            return cls._member_visitor_instance


class AbstractVisitor(ABC, ast.NodeVisitor):
    def __init__(self):
        self.module = None
        self.discovered_modules = DiscoveredModules.get_instance()
        super().__init__()

    def generic_visit(self, node):
        # print(type(node).__name__)
        ast.NodeVisitor.generic_visit(self, node)

    def set_module(self, module: 'importUnit.ModuleUnit'):
        self.module = module


class _ImportVisitor(AbstractVisitor):
    def visit_Import(self, node):
        for alias in node.names:
            # TODO: put this check into ImportUnit`s code
            if alias.name in self.discovered_modules:
                module = self.discovered_modules[alias.name]
            else:
                # TODO: handle external modules dependencies
                module = alias.name + " [External]"

            self.module.imports.add(ImportUnit(alias, module))
        AbstractVisitor.generic_visit(self, node)

    def visit_ImportFrom(self, node):
        self.visit_Import(node)


class _MemberVisitor(AbstractVisitor):
    def visit_FunctionDef(self, node):
        # print('function', node.name)
        self.module.namespace.append((node.name, 'function'))
        # ast.NodeVisitor.generic_visit(self, node)

    def visit_ClassDef(self, node):
        # print('class', node.name)
        self.module.namespace.append((node.name, 'class'))
        # ast.NodeVisitor.generic_visit(self, node)

    def visit_Assign(self, node):
        # print('Found global in', self.module.full_name)

        for t in node.targets:
            if isinstance(t, tuple):
                for tt in t[0]:
                    self.module.namespace.append((tt.id, 'global variable'))
                    # print(tt.id)
            elif isinstance(t, _ast.Name):
                self.module.namespace.append((t.id, 'global variable'))
                # print(t.id)
            # else:
                # print(type(t))

    def visit_AugAssign(self, node):
        print('It\'s an aug assign!')
        self.visit_Assign(node)
