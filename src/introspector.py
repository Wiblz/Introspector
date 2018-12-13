import importlib
import pickle
import pkgutil
from pprint import pprint

import sys

from src.DiscoveredModules import DiscoveredModules
from src.importUnit import FromImportUnit, ModuleImportUnit
from src.module import ModuleUnit, ExternalModule

# path = r"/home/counterfeit/Projects/test/"
# path = r"/home/counterfeit/Projects/Introspector/src/"
path = r"/home/counterfeit/Projects/Introspector/"

# path = r"/usr/lib/python3.6/"
# path = r"/home/counterfeit/.IntelliJIdea2018.2/config/plugins/python/helpers/typeshed/stdlib/2and3/"

debug_mode = False
discovered_modules = DiscoveredModules.get_instance()

# TODO: enable pickling scanning result for testing purposes


def discover(packages_string, path_string, offset, name):
    full_name = _f(name, packages_string)
    if full_name in discovered_modules:
        return discovered_modules[full_name]

    discovered_modules[full_name] = ModuleUnit(name,
                                               full_name,
                                               _p(path_string))
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
            # remote_import(packages_string, path_string, offset, i.name)
            discover(packages_string, path_string, offset, i.name)
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

    sys.path.insert(0, path)

    list_modules()
    print('------------------------------------------\n\n\n\n')
    for v in discovered_modules.values():
        v.get_imports()

    print(len(discovered_modules))

    for v in discovered_modules.values():
        print('MODULE', v.full_name)
        for i in v.imports:
            print(i)
        print('-----------------------------\n\n')

    find_redundancy()

    # with open('chains', 'a+') as file:
    #     for v in discovered_modules.values():
    #         print(v.full_name, '   ', len(v.imports))
    #         import_chain(v, file)
    #         # v.dump_to_file()


# TODO: Refactor hard!
def import_chain(module: 'ModuleUnit or ExternalModule', file, path=[]):
    cycle = module.full_name in path
    if not cycle:
        path.append(module.full_name)
    # print(resolved_name)

    if isinstance(module, ExternalModule) or not module.imports:
        _write_chain(file, path)
    elif cycle:
        if not discovered_modules[path[-1]].written:
            _write_chain(file, path)
            discovered_modules[path[-1]].written = True
    else:
        for imp in module.imports:
            # if imp.module.full_name not in path:
            import_chain(imp.module, file, path)

    if not cycle:
        if isinstance(module, ModuleUnit) and module.written:
            module.written = False
        _pop(path)


def find_redundancy():
    with open('redundancy', 'a+') as file:
        for v in discovered_modules.values():
            file.write('MODULE ' + v.full_name + '\n\n')
            fine = True
            for imp in v.imports:
                if (isinstance(imp, FromImportUnit) and not imp.used) or isinstance(imp, ModuleImportUnit):
                    fine = False
                    file.write(imp.__str__() + '\n')
            if fine:
                file.write('This module\'s imports are fine')
            file.write('\n\n-------------------------------\n')


def _write_chain(file, path):
    for index in range(len(path) - 1):
        file.write(path[index])
        file.write(' --> ')
    file.write(path[len(path) - 1])
    file.write('\n\n')


if __name__ == '__main__':
    main()
