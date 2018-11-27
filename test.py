import ast
import importlib
import inspect
import pkgutil
import sys


# path = r"/home/counterfeit/Projects/test/"
path = r"/usr/lib/python3.6/"
# path = r"/home/counterfeit/.IntelliJIdea2018.2/config/plugins/python/helpers/typeshed/stdlib/2and3/"

debug_mode = False
discovered_modules = dict()


# TODO: enable pickling scanning result for testing purposes

class Module:
    def __init__(self, name, full_name, path, module_instance=None):
        self.name = name
        self.full_name = full_name
        self.path = path
        self.namespace = dict()
        self.module_instance = module_instance
        self.imports = set()

    def __str__(self):
        return "[" + self.name + ",\n" + self.path + ",\n" + str(self.namespace) + ",\n" + str(self.module_instance is
                                                                                               not None) + "]"

    def __repr__(self):
        return self.__str__()

    def get_namespace(self):
        if self.module_instance:
            self.namespace = [x for x in inspect.getmembers(self.module_instance) if x[0] != '__builtins__']


class Visitor(ast.NodeVisitor):
    def visit_Import(self, node):
        a = self.m.path + self.m.name
        # print(node.names[0].name, node.names[0].asname)
        for alias in node.names:
            discovered_modules[self.m.full_name].imports.add(ImportUnit(alias))

    def visit_ImportFrom(self, node):
        self.visit_Import(node)


class ImportUnit:
    def __init__(self, alias):
        if alias.name in discovered_modules:
            self.module = discovered_modules[alias.name]
        else:
            # TODO: handle external modules dependencies
            self.module = alias.name + " [External]"

        if alias.asname is not None:
            self.alias = alias.asname

        # TODO: handle 'from' imports

    def __hash__(self):
        if isinstance(self.module, str):
            return hash(self.module)

        _hash = self.module.full_name
        if hasattr(self, 'alias'):
            _hash += self.alias
        if hasattr(self, 'members'):
            _hash += self.members
        return hash(_hash)

    def __str__(self):
        return "[" +\
               (self.module if isinstance(self.module, str) else self.module.full_name) +\
               (self.alias if hasattr(self, 'alias') else 'None') +\
               (self.members if hasattr(self, 'members') else 'None') + "]"

    def __repr__(self):
        return self.__str__()


def remote_import(packages_string, path_string, offset, name):
    if _f(name, packages_string) in discovered_modules:
        return
    if name in sys.modules:
        del sys.modules[name]

    try:
        full_name = _f(name, packages_string)
        try:
            imported_module = importlib.import_module(name)
        except Exception:
            print("Error of absolute import")
            imported_module = importlib.import_module('.' + name, package=packages_string)

        discovered_modules[full_name] = Module(name,
                                               full_name,
                                               _p(path_string),
                                               imported_module)
    except Exception as e:
        # TODO: retrieve module members using AST
        print("Error of relative import   ", packages_string, ".", name, sep='')
        with open('errors', 'a+') as f:
            f.write(path + path_string + '\n' + packages_string + "." + name + "\n" + str(e.__class__) + "\n" + str(e) +
                    "\n\n\n")


def list_modules(packages=[], offset=0):
    packages_string = '.'.join(packages)
    path_string = '/'.join(packages)
    sys.path.append(path + path_string)

    if debug_mode:
        print('\t' * (offset - 1), packages_string, sep='')

    for i in pkgutil.iter_modules([path + path_string]):
        if i.name == "__main__":
            continue
        if i.ispkg:
            packages.append(i.name)
            list_modules(packages, offset + 1)
        else:
            remote_import(packages_string, path_string, offset, i.name)

    _pop(packages)


def main():
    # print(importlib.util.find_spec('copy').loader.load_module())
    # pprint(sys.builtin_module_names)
    # pprint(sys.modules)

    # print('rlcompleter' in sys.modules)
    # sys.meta_path = []
    # sys.path = [path]

    sys.path.insert(0, path)

    # a = importlib.util.find_spec('functools')
    # a = importlib.util._find_spec_from_path('functools', path)
    # pprint(a if a is None else inspect.getmembers(a))

    x = Visitor()

    list_modules()
    for v in discovered_modules.values():
        v.get_namespace()
        x.m = v
        x.visit(_get_ast(v))
        with open('output/' + v.name, 'w+') as f:
            f.write("MODULE " + v.full_name + " NAMESPACE\n\n\n")
            for i in v.namespace:
                f.write(str(i) + '\n')

    for i in discovered_modules['base64'].imports:
        print(i)

# imported_module = importlib.import_module('functools')
    # a = inspect.getmembers(imported_module)
    # a = [x for x in a if x[0] != '__builtins__']
    # pprint(a)


def _get_ast(module: 'Module'):
    with open(module.path + module.name + '.py') as f:
        a = f.read()

    return ast.parse(a)


def _check_shadowing_builtin():
    pass


def _pop(l):
    if l:
        l.pop()


def _f(name, package_string):
    """Construct full name for the module

    This is helper function for constructing full name of modules
    having file name and parent packages in form of package string.
    It has such name to make numerous calls of it a little bit more concise.

    """
    return package_string + '.' + name if package_string else name


def _p(path_string):
    return path + path_string + '/' if path_string else path


if __name__ == '__main__':
    main()
