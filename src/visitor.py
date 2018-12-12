import ast
from abc import ABC, abstractmethod
from pprint import pprint

import _ast

from src.DiscoveredModules import DiscoveredModules
from src.importUnit import ModuleImportUnit
from src.importUnit import FromImportUnit
import src.importUnit as importUnit


class Visitors:
    _import_visitor_instance = None
    _member_visitor_instance = None

    def __new__(cls, *args, **kwargs):
        raise RuntimeError('%s should not be instantiated. Use "get_instance" instead' % cls)

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
    @abstractmethod
    def __init__(self):
        self.module = None
        self.discovered_modules = DiscoveredModules.get_instance()
        super().__init__()

    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)

    def set_module(self, module: 'importUnit.ModuleUnit'):
        self.module = module


def resolve_relative_import(current_name, imported_name, level):
    if level == 0:
        return imported_name
    else:
        index = 0
        for index, char in reversed(list(enumerate(current_name))):
            if char == '.':
                level -= 1
                if level == 0: break
        if index == 0:
            return imported_name
        else:
            return current_name[0:index+1] + imported_name


class _ImportVisitor(AbstractVisitor):
    def __init__(self):
        super().__init__()
        self.namespace_stack = [dict()]

    def add_imports(self, node, level=None):
        from src.module import ExternalModule
        inner = len(self.namespace_stack) != 0

        for alias in node.names:
            if level is None:
                resolved_name = alias.name
            else:
                if node.module is None:
                    resolved_name = resolve_relative_import(self.module.full_name, alias.name, level)

                    # FIXME: this is an ugly kludge to create ModuleImportUnit
                    # instead of FromImportUnit at the end of this function
                    level = None
                else:
                    resolved_name = resolve_relative_import(self.module.full_name, node.module, level)

            if resolved_name in self.discovered_modules:
                module = self.discovered_modules[resolved_name]
            else:
                # TODO: handle external modules dependencies
                module = ExternalModule(resolved_name)

            if alias.name == '*' and not isinstance(module, ExternalModule):
                for item in module.namespace:
                    import_unit = FromImportUnit(alias.asname, item[0], module, node.lineno, inner)
                    self.module.imports.add(import_unit)
                    self.namespace_stack[-1][import_unit.get_ref()] = import_unit
            else:
                if level is None:
                    import_unit = ModuleImportUnit(alias.asname, module, node.lineno, inner)
                else:
                    import_unit = FromImportUnit(alias.asname, alias.name, module, node.lineno, inner)

                self.module.imports.add(import_unit)
                self.namespace_stack[-1][import_unit.get_ref()] = import_unit

    def visit_Import(self, node):
        self.add_imports(node)
        AbstractVisitor.generic_visit(self, node)

    def visit_ImportFrom(self, node):
        self.add_imports(node, node.level)
        AbstractVisitor.generic_visit(self, node)

    def visit_FunctionDef(self, node):
        self.namespace_stack.append(dict())
        ast.NodeVisitor.generic_visit(self, node)
        self.namespace_stack.pop()

    def visit_ClassDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Name(self, node):
        for namespace in reversed(self.namespace_stack):
            if node.id in namespace and isinstance(namespace[node.id], FromImportUnit):
                namespace[node.id].used = True
                del namespace[node.id]
                break

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name):
            for namespace in reversed(self.namespace_stack):
                if node.value.id in namespace and isinstance(namespace[node.value.id], ModuleImportUnit):
                    namespace[node.value.id].names_used.append(node.attr)
                    del namespace[node.value.id]
                    break

    # def generic_visit(self, node):
    #     node_type = type(node)


class _MemberVisitor(AbstractVisitor):
    def __init__(self):
        super().__init__()

    def visit_FunctionDef(self, node):
        self.module.namespace.append((node.name, 'function'))

    def visit_ClassDef(self, node):
        self.module.namespace.append((node.name, 'class'))

    def visit_Assign(self, node):
        for t in node.targets:
            if isinstance(t, tuple):
                for tt in t[0]:
                    self.module.namespace.append((tt.id, 'global variable'))
                    # print(tt.id)
            elif isinstance(t, _ast.Name):
                self.module.namespace.append((t.id, 'global variable'))
