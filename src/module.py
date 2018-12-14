import ast
import inspect
import os
from fileinput import filename

__next_number__ = -1


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
        self._get_namespace()
        self.number = __next_number__

    def __str__(self):
        return 'module '

    def __repr__(self):
        return self.__str__()

    def _get_namespace(self):
        from src.visitor import Visitors

        visitor = Visitors.get_instance()
        visitor.set_module(self)
        visitor.visit(self.ast)

    def add_import(self, import_unit):
        if not import_unit.inner:
            self.namespace.append((import_unit.get_ref(), 'imported object'))

        self.imports.add(import_unit)

    def get_imports(self):
        from src.visitor import Visitors

        if self.full_name == 'aifc':
            print()

        visitor = Visitors.get_instance(True)
        visitor.set_module(self)
        visitor.visit(self.ast)

    def set_number(self):
        global __next_number__
        __next_number__ += 1
        self.number = __next_number__

    def dump_to_file(self):
        os.makedirs(os.path.dirname('output/namespaces/' + self.full_name), exist_ok=True)
        with open('output/namespaces/' + self.full_name, 'w') as file:
            file.write("MODULE " + self.full_name + " NAMESPACE\n\n\n")
            if self.namespace:
                f = list()
                c = list()
                v = list()
                i = list()
                for item in self.namespace:
                    if item[1] == 'function':
                        f.append(item)
                    elif item[1] == 'class':
                        c.append(item)
                    elif item[1] == 'global variable':
                        v.append(item)
                    else:
                        i.append(item)

                for item in f:
                    file.write(str(item) + '\n')
                if f: file.write('\n')

                for item in c:
                    file.write(str(item) + '\n')
                if c: file.write('\n')

                for item in v:
                    file.write(str(item) + '\n')
                if v: file.write('\n')

                for item in i:
                    file.write(str(item) + '\n')


class ExternalModule:
    def __init__(self, full_name):
        self.number = __next_number__
        self.full_name = full_name
        index = full_name.rfind('.')
        if index == -1:
            self.name = full_name
        else:
            self.name = full_name[index + 1:]

    def set_number(self):
        global __next_number__
        __next_number__ += 1
        self.number = __next_number__


def _get_ast(module: 'ModuleUnit'):
    with open(module.path + module.name + '.py') as f:
        a = f.read()

    return ast.parse(a)
