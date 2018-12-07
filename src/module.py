import ast
import inspect


class ModuleUnit:
    def __init__(self, name, full_name, path, module_instance=None):
        self.name = name
        self.full_name = full_name
        self.path = path
        self.namespace = dict()
        self.module_instance = module_instance
        self.imports = set()

        if module_instance is None:
            self.ast = _get_ast(self)

    def __str__(self):
        return "[" + self.name + ",\n" + self.path + ",\n" + str(self.namespace) + ",\n" + str(self.module_instance is
                                                                                               not None) + "]"

    def __repr__(self):
        return self.__str__()

    def get_namespace(self):
        if self.module_instance:
            self.namespace = [x for x in inspect.getmembers(self.module_instance) if x[0] != '__builtins__']
        else:
            self.namespace = _get_members(self.ast)


def _get_members(ast):
    pass


def _get_ast(module: 'Module'):
    with open(module.path + module.name + '.py') as f:
        a = f.read()

    return ast.parse(a)
