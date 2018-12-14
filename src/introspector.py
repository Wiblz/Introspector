import importlib
import os
import pickle
import pkgutil
from pprint import pprint

import sys

from src.DiscoveredModules import DiscoveredModules
from src.importUnit import FromImportUnit, ModuleImportUnit
from src.module import ModuleUnit, ExternalModule

debug_mode = False
discovered_modules = DiscoveredModules.get_instance()


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
        return l.pop()


def _f(name, package_string):
    """Construct full name for the module.py

    This is a helper function for constructing full name of modules
    having file name and parent packages in form of package string.
    It has such name to make numerous calls of it a little bit more concise.

    """
    return package_string + '.' + name if package_string else name


def _p(path_string):
    return path + path_string + '/' if path_string else path


def print_help():
    print('Usage: introspector.py <path to package> [n c d r all]')
    exit(-2)


def get_namespaces():
    for module in discovered_modules.values():
        module.dump_to_file()


def get_chains():
    for module in discovered_modules.values():
        os.makedirs(os.path.dirname('output/chains/' + module.full_name), exist_ok=True)
        with open('output/chains/' + module.full_name, 'w') as file:
            file.write("MODULE " + module.full_name + " IMPORT CHAINS\n\n\n")
            print(module.full_name, '   ', len(module.imports))
            import_chain(module, file)


def get_dependencies():
    for module in discovered_modules.values():
        if module.full_name == 'aifc':
            print()
        os.makedirs(os.path.dirname('output/dependencies/' + module.full_name), exist_ok=True)
        with open('output/dependencies/' + module.full_name, 'w') as file:
            file.write("MODULE " + module.full_name + " DEPENDENCIES\n\n\n")
            for import_unit in module.imports:
                if isinstance(import_unit, FromImportUnit):
                    if import_unit.used:
                        file.write('Name \'' + import_unit.item
                                   + ('\' imported as ' + import_unit.alias if import_unit.alias else '\'') + ' from \'' +
                                   import_unit.module.full_name + '\' module was used.')
                        file.write('\n')
                else:
                    if import_unit.used:
                        file.write('Module \'' + import_unit.module.full_name
                                   + '\' object' + ('as' + import_unit.alias if import_unit.alias else '') + ' was used.')
                        file.write('\n')
                    for name in import_unit.names_used:
                        file.write('Name \'' + name + '\' as module \'' + import_unit.module.full_name + '\' attribute was used.')
                        file.write('\n')


def find_redundancy():
        for module in discovered_modules.values():
            if module.full_name == 'aifc':
                for imp in module.imports:
                    print(imp)

            os.makedirs(os.path.dirname('output/redundancy/' + module.full_name), exist_ok=True)
            with open('output/redundancy/' + module.full_name, 'w') as file:
                file.write('MODULE ' + module.full_name + '\n\n')
                fine = True
                for imp in module.imports:
                    if (isinstance(imp, FromImportUnit) and not imp.used) or isinstance(imp, ModuleImportUnit):
                        fine = False
                        file.write(imp.__str__() + '\n')
                if fine:
                    file.write('This module\'s imports are fine')


def main(argv):
    # 'namespaces', 'chains', 'dependencies', 'redundancy' or everything at once
    if len(argv) < 2 or argv[1] not in ['n', 'c', 'd', 'r', 'all']:
        print_help()

    global path
    path = argv[0]

    list_modules()
    for v in discovered_modules.values():
        v.get_imports()

    print(len(discovered_modules), 'modules found.')

    if argv[1] == 'n':
        get_namespaces()
    elif argv[1] == 'c':
        get_chains()
    elif argv[1] == 'd':
        get_dependencies()
    elif argv[1] == 'r':
        find_redundancy()
    else:
        get_namespaces()
        get_chains()
        get_dependencies()
        find_redundancy()


def import_chain(module: 'ModuleUnit or ExternalModule', file, depth=0, path=[]):
    path.append(module.full_name)
    if module.number != -1:
        _write_chain(file, path, depth, module.number)
        return

    if isinstance(module, ExternalModule) or not module.imports:
        _write_chain(file, path, depth)
    else:
        valid_chains = list()
        for imp in module.imports:
            if isinstance(imp, ModuleImportUnit) and imp.module.full_name not in path:
                valid_chains.append(imp)

        if len(valid_chains) == 0:
            _write_chain(file, path, depth)

        elif len(valid_chains) > 1:
            module.set_number()
            _write_chain(file, path, depth)
            for imp in valid_chains:
                import_chain(imp.module, file, len(path), path)
        else:
            module.set_number()
            import_chain(valid_chains[0].module, file, depth, path)

    _pop(path)


def _write_chain(file, path, depth=0, number=None):
    for index in range(depth - 1):
        file.write((len(path[index]) + 5) * ' ')

    if depth != 0:
        file.write(len(path[depth - 1]) * ' ' + ' --> ')

    for index in range(depth, len(path) - 1):
        if path[index] in discovered_modules and discovered_modules[path[index]].number != -1:
            file.write('[' + str(discovered_modules[path[index]].number) + '] ')
        file.write(path[index])
        file.write(' --> ')

    if path[-1] in discovered_modules and discovered_modules[path[-1]].number != -1:
        file.write('[' + str(discovered_modules[path[-1]].number) + '] ')
    file.write(path[-1])
    if number is not None:
        file.write(' (watch ' + str(number) + ')')
    file.write('\n')


if __name__ == '__main__':
    file_dir = os.path.dirname(__file__)
    sys.path.append(file_dir)
    main(sys.argv[1:])
