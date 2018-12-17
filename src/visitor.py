"""Ast visitors for namespace fetching ('_MemberVisitor')
and for imports and their usage analyzing ('_ImportVisitor').
Both are singletons and are contained in the 'Visitors' class.

"""

import ast
import _ast
import src.import_units as import_units

from abc import ABC, abstractmethod
from src.discovered_modules import DiscoveredModules
from src.import_units import ModuleImportUnit
from src.import_units import FromImportUnit
from src.util import _add, resolve_relative_import


class Visitors:
    """Container for singleton ast visitor classes."""
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
    """Abstract base ast node visitor class.

    Contains 'Module' object of the module that is being analyzed at the moment
    and a reference to dictionary with discovered modules.

    """

    @abstractmethod
    def __init__(self):
        self.module = None
        self.discovered_modules = DiscoveredModules.get_instance()
        super().__init__()

    def generic_visit(self, node):
        ast.NodeVisitor.generic_visit(self, node)

    def set_module(self, module: 'import_units.ModuleUnit'):
        self.module = module


class _ImportVisitor(AbstractVisitor):
    """Ast visitor for finding imports in modules and tracking of their usages."""

    def __init__(self):
        super().__init__()
        self.namespace_stack = [dict()]

    def add_imports(self, node, level=None):
        """Handle import statements.

        Resolve all possible kinds of imports, construct corresponding 'ImportUnit' instances
        and put them in the 'Module' being processed. Unpack '*' imports in separate
        'FromImportUnit' objects where it is possible.

        :param node: ast node with import statement, either ast.Import or ast.ImportFrom
        :param level: relative import level, 0 for absolute import
        """

        from src.module_units import ExternalModule
        # are we in the outermost (global) namespace?
        inner = len(self.namespace_stack) > 1

        # loop through all names being imported in single statement
        for alias in node.names:

            if level is None:
                resolved_name = alias.name
            else:
                # handle relative import case

                if node.module is None:
                    resolved_name = resolve_relative_import(self.module.full_name, alias.name, level)
                    level = None
                else:
                    resolved_name = resolve_relative_import(self.module.full_name, node.module, level)

            # 'module' can represent imported module or the one from which
            # other names are imported depending on context.
            # Here we check if 'module' is external
            if resolved_name in self.discovered_modules:
                module = self.discovered_modules[resolved_name]
            else:
                module = ExternalModule(resolved_name)

            if alias.name == '*' and not isinstance(module, ExternalModule):
                # unpacking asterisk import
                for item in module.namespace:
                    import_unit = FromImportUnit(alias.asname, item[0], module, node.lineno, inner)
                    self.module.add_import(import_unit)
                    self.namespace_stack[-1][import_unit.get_ref()] = import_unit
            else:
                if level is None:
                    import_unit = ModuleImportUnit(alias.asname, module, node.lineno, inner)
                else:
                    import_unit = FromImportUnit(alias.asname, alias.name, module, node.lineno, inner)

                # add created import unit to 'Module' object
                self.module.add_import(import_unit)
                # put imported name(s) into current scope
                self.namespace_stack[-1][import_unit.get_ref()] = import_unit

    def shadow_name(self, name):
        """Check if 'name' is already defined in innermost namespace
         and set the 'shadowed' flag on 'Module' that had used this name"""

        if name in self.namespace_stack[-1]:
            self.namespace_stack[-1][name].shadowed = True

    def visit_Import(self, node):
        self.add_imports(node)

    def visit_ImportFrom(self, node):
        self.add_imports(node, node.level)

    def visit_FunctionDef(self, node):
        """Handling 'def' statement.

        Check if function name shadows imports,
        create new namespace,
        visit all child ast nodes with 'generic_visit' call,
        destroy function namespace.
        """

        self.shadow_name(node.name)
        self.namespace_stack.append(dict())
        ast.NodeVisitor.generic_visit(self, node)
        self.namespace_stack.pop()

    def visit_ClassDef(self, node):
        """Class definitions are handled in a same way as functions."""

        self.visit_FunctionDef(node)

    def visit_Name(self, node):
        """Check if name usage is shadowing, rewriting or usage of the imported names"""

        # something was assigned to variable that previously stored imported item
        if node.ctx == ast.Store():
            self.shadow_name(node.id)

        # check imported names in all scopes
        for namespace in reversed(self.namespace_stack):
            if node.id in namespace:
                if not namespace[node.id].shadowed:
                    namespace[node.id].used = True

                    if isinstance(namespace[node.id], FromImportUnit):
                        # we no longer need to track names imported with 'from'
                        # statement as they have already been used
                        del namespace[node.id]
                break

    def visit_Attribute(self, node):
        """Check if attribute usage is corresponding to names in imported modules"""

        # case of multiple level attribute referencing
        # i.e. taking attribute of an attribute
        while isinstance(node.value, ast.Attribute):
            node = node.value

        if isinstance(node.value, ast.Name):
            for namespace in reversed(self.namespace_stack):
                if node.value.id in namespace and isinstance(namespace[node.value.id], ModuleImportUnit):
                    # name, attribute of which was referenced is imported module

                    # tell 'Module' that some name was used as it's attribute
                    namespace[node.value.id].resolve_name_used(node.attr)
                    break


class _MemberVisitor(AbstractVisitor):
    """Ast visitor for module namespaces fetching."""

    def __init__(self):
        super().__init__()

    def visit_FunctionDef(self, node):
        self.module.namespace.append((node.name, 'function'))

    def visit_ClassDef(self, node):
        self.module.namespace.append((node.name, 'class'))

    def visit_Assign(self, node):
        """Top level (global) assigns handler."""
        for t in node.targets:
            # multiple assignment case
            if isinstance(t, tuple):
                for tt in t[0]:
                    _add(self.module.namespace, (tt.id, 'global variable'))
            elif isinstance(t, _ast.Name):
                _add(self.module.namespace, (t.id, 'global variable'))
