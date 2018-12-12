import ast
import inspect

from src.visitor import Visitors


class ModuleUnit:
    def __init__(self, name, full_name, path, module_instance=None):
        self.name = name
        self.full_name = full_name
        self.path = path
        self.namespace = []
        self.module_instance = module_instance
        self.imports = set()
        self.ast = _get_ast(self)
        self.written = False

        if module_instance is None:
            self._get_namespace_manually()
        else:
            self._get_namespace()

    def __str__(self):
        return "[" + self.name + ",\n" + self.path + ",\n" + str(self.namespace) + ",\n" + str(self.module_instance is
                                                                                               not None) + "]"

    def __repr__(self):
        return self.__str__()

    def _get_namespace(self):
        self.namespace = [x for x in inspect.getmembers(self.module_instance) if not x[0].startswith('__')]

    def _get_namespace_manually(self):
        visitor = Visitors.get_instance()
        visitor.set_module(self)
        visitor.visit(self.ast)

    def get_imports(self):
        visitor = Visitors.get_instance(True)
        visitor.set_module(self)
        visitor.visit(self.ast)

    def dump_to_file(self):
        with open('output/' + self.full_name, 'w+') as f:
            f.write("MODULE " + self.full_name + " NAMESPACE\n\n\n")
            if self.namespace:
                for i in self.namespace:
                    f.write(str(i) + '\n')


class ExternalModule:
    def __init__(self, full_name):
        self.full_name = full_name
        index = full_name.rfind('.')
        if index == -1:
            self.name = full_name
        else:
            self.name = full_name[index + 1:]


def _get_ast(module: 'ModuleUnit'):
    with open(module.path + module.name + '.py') as f:
        a = f.read()

    return ast.parse(a)
