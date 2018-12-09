import importlib
import pickle
import pkgutil
import sys

from src.DiscoveredModules import DiscoveredModules
from src.module import ModuleUnit


# path = r"/home/counterfeit/Projects/test/"
# path = r"/home/counterfeit/Projects/Introspector/src/"

path = r"/usr/lib/python3.6/"
# path = r"/home/counterfeit/.IntelliJIdea2018.2/config/plugins/python/helpers/typeshed/stdlib/2and3/"

debug_mode = False
discovered_modules = DiscoveredModules.get_instance()

# TODO: enable pickling scanning result for testing purposes


def remote_import(packages_string, path_string, offset, name):
    if _f(name, packages_string) in discovered_modules:
        return
    if name in sys.modules:
        del sys.modules[name]

    imported_module = None
    full_name = _f(name, packages_string)
    try:
        imported_module = importlib.import_module(full_name)
    except Exception:
        if debug_mode:
            print("Error of absolute import")
        try:
            imported_module = importlib.import_module('.' + name, package=packages_string)
        except Exception as e:
            if debug_mode:
                print("Error of relative import   ", packages_string, ".", name, sep='')

            with open('errors', 'a+') as f:
                f.write(path + path_string + '\n' + packages_string + "." + name + "\n" + str(e.__class__) + "\n" + str(e) +
                        "\n\n\n")

    discovered_modules[full_name] = ModuleUnit(name,
                                               full_name,
                                               _p(path_string),
                                               imported_module)
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
    """Pop an element from the list if it is not empty.

    This is a helper function for safe item popping from the list

    """
    if l:
        l.pop()


def _f(name, package_string):
    """Construct full name for the module.py

    This is a helper function for constructing full name of modules
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

    list_modules()
    print('------------------------------------------\n\n\n\n')
    for v in discovered_modules.values():
        v.get_imports()

    with open('chains', 'a+') as file:
        for v in discovered_modules.values():
            print(v.full_name, '   ', len(v.imports))
            import_chain(v, file)
            # v.dump_to_file()

    # with open('data.pickle', 'wb') as f:
    #     pickle.dump(discovered_modules, f)

    print(len(discovered_modules))

    # imported_module = importlib.import_module('functools')
    # a = inspect.getmembers(imported_module)
    # a = [x for x in a if x[0] != '__builtins__']
    # pprint(a)


def import_chain(module: 'ModuleUnit', file, path=[]):
    resolved_name = module.full_name if isinstance(module, ModuleUnit) else module
    if resolved_name in path:
        return
    # print(resolved_name)
    path.append(resolved_name)

    if isinstance(module, str) or not module.imports:
        for index in range(len(path) - 1):
            file.write(path[index])
            file.write(' --> ')
        file.write(path[len(path) - 1])
        file.write('\n\n')
    else:
        for imp in module.imports:
            # if imp.module.full_name not in path:
            import_chain(imp.module, file, path)

    _pop(path)


if __name__ == '__main__':
    main()
