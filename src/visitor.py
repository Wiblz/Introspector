import ast

from importUnit import ImportUnit
from introspector import discovered_modules
from module import ModuleUnit


class Visitor(ast.NodeVisitor):
    def __init__(self, module: 'ModuleUnit'):
        self.module = module
        super().__init__()

    def visit_Import(self, node):
        for alias in node.names:
            discovered_modules[self.module.full_name].imports.add(ImportUnit(alias))

    def visit_ImportFrom(self, node):
        self.visit_Import(node)
