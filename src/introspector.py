import ast
import importlib
import pkgutil
import sys
from module import _get_ast, ModuleUnit
import importUnit


# path = r"/home/counterfeit/Projects/test/"
# path = r"/home/counterfeit/Projects/Introspector/"

path = r"/usr/lib/python3.6/"
# path = r"/home/counterfeit/.IntelliJIdea2018.2/config/plugins/python/helpers/typeshed/stdlib/2and3/"

debug_mode = False
discovered_modules = dict()


# TODO: enable pickling scanning result for testing purposes


def remote_import(packages_string, path_string, offset, name):
    if _f(name, packages_string) in discovered_modules:
        return
    if name in sys.modules:
        del sys.modules[name]

    full_name = _f(name, packages_string)
    try:
        try:
            imported_module = importlib.import_module(name)
        except Exception:
            print("Error of absolute import")
            imported_module = importlib.import_module('.' + name, package=packages_string)

        discovered_modules[full_name] = ModuleUnit(name,
                                                   full_name,
                                                   _p(path_string),
                                                   imported_module)
        return discovered_modules[full_name]

    except Exception as e:
        # TODO: retrieve module.py members using AST
        print("Error of relative import   ", packages_string, ".", name, sep='')
        discovered_modules[full_name] = ModuleUnit(name,
                                                   full_name,
                                                   _p(path_string),
                                                   None)

        with open('errors', 'a+') as f:
            f.write(path + path_string + '\n' + packages_string + "." + name + "\n" + str(e.__class__) + "\n" + str(e) +
                    "\n\n\n")

        return discovered_modules[full_name]


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


def _pop(l):
    if l:
        l.pop()


def _f(name, package_string):
    """Construct full name for the module.py

    This is helper function for constructing full name of modules
    having file name and parent packages in form of package string.
    It has such name to make numerous calls of it a little bit more concise.

    """
    return package_string + '.' + name if package_string else name


def _p(path_string):
    return path + path_string + '/' if path_string else path


def main():
    import sys

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


if __name__ == '__main__':
    main()
