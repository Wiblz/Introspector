import os
import pkgutil
import sys

from src import module_units
from src.discovered_modules import DiscoveredModules
from src.import_units import FromImportUnit, ModuleImportUnit
from src.module_units import ModuleUnit, ExternalModule
from src.util import _pop

discovered_modules = DiscoveredModules.get_instance()


def discover(packages_string, path_string, name):
    """Construct 'Module' object resolving path to it and it's full name"""

    full_name = packages_string + '.' + name if packages_string else name
    if full_name in discovered_modules:
        return discovered_modules[full_name]

    discovered_modules[full_name] = ModuleUnit(name,
                                               full_name,
                                               path + path_string + '/' if path_string else path)
    return discovered_modules[full_name]


def list_modules(packages=[], offset=0):
    """Recursively walk through packages and find all modules"""

    packages_string = '.'.join(packages)
    path_string = '/'.join(packages)
    sys.path.append(path + path_string)

    for i in pkgutil.iter_modules([path + path_string]):
        if i.name == "__main__":
            continue
        if i.ispkg:
            packages.append(i.name)
            list_modules(packages, offset + 1)
        else:
            # remote_import(packages_string, path_string, offset, i.name)
            discover(packages_string, path_string, i.name)

    _pop(packages)


def print_help():
    print('Usage: introspector.py <path to package> [n c d r all]')
    exit(-2)


def get_namespace(file, module):
    """Write module's namespace to file in pretty way."""

    file.write("MODULE " + module.full_name + " NAMESPACE\n\n\n")
    if module.namespace:
        # divide names by type

        f = list()
        c = list()
        v = list()
        i = list()
        for item in module.namespace:
            if item[1] == 'function':
                f.append(item)
            elif item[1] == 'class':
                c.append(item)
            elif item[1] == 'global variable':
                v.append(item)
            else:
                i.append(item)

        for item in f:
            file.write(item[0] + ': ' + item[1] + '\n')
        if f: file.write('\n')

        for item in c:
            file.write(item[0] + ': ' + item[1] + '\n')
        if c: file.write('\n')

        for item in v:
            file.write(item[0] + ': ' + item[1] + '\n')
        if v: file.write('\n')

        for item in i:
            file.write(item[0] + ': ' + item[1] + '\n')


def get_chain(file, module):
    """Write import chains beginning with 'module' to file"""

    file.write("MODULE " + module.full_name + " IMPORT CHAINS\n\n\n")
    import_chain(module, file)
    _purge_numbers()


def get_dependency(file, module):
    """Write functional dependencies of 'module' to file"""

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


def find_redundancy(file, module):
    """Find redundancy in module's imports and write report to file"""

    file.write('MODULE ' + module.full_name + '\n\n')
    fine = True
    for imp in module.imports:
        if (isinstance(imp, FromImportUnit) and not imp.used) or isinstance(imp, ModuleImportUnit):
            fine = False
            file.write(imp.__str__() + '\n')
    if fine:
        file.write('This module\'s imports are fine')


def _for_each(dir, func):
    """Walk through discovered modules, open file and call 'func' for each"""

    for module in discovered_modules.values():
        os.makedirs(os.path.dirname(dir + module.full_name), exist_ok=True)
        with open(dir + module.full_name, 'w') as file:
            func(file, module)


def main(argv):
    if argv and argv[0] in ['--help', '-help', 'help', '-h', 'h', '?']:
        print_help()

    if len(argv) < 2:
        print('Too few arguments to use Introspector.')
        print_help()
    elif not os.path.isdir(argv[0]):
        print('Can\'t find a package directory at', argv[1])
        print_help()

    # 'namespaces', 'chains', 'dependencies', 'redundancy' or everything at once
    elif argv[1] not in ['n', 'c', 'd', 'r', 'all']:
        print('Unknown argument \'', argv[1], '\'', sep='')
        print_help()

    global path
    path = argv[0]
    if not path.endswith('/'):
        path += '/'

    list_modules()
    for v in discovered_modules.values():
        v.get_imports()

    print(len(discovered_modules), 'modules found.')

    if argv[1] == 'n':
        _for_each('output/namespaces/', get_namespace)
    elif argv[1] == 'c':
        _for_each('output/chains/', get_chain)
    elif argv[1] == 'd':
        _for_each('output/dependencies/', get_dependency)
    elif argv[1] == 'r':
        _for_each('output/redundancy/', find_redundancy)
    else:
        _for_each('output/namespaces/', get_namespace)
        _for_each('output/chains/', get_chain)
        _for_each('output/dependencies/', get_dependency)
        _for_each('output/redundancy/', find_redundancy)


def import_chain(module: 'Module', file, depth=0, path=[]):
    """Recursively build an import chain beginning in 'module'"""

    path.append(module.full_name)

    if module.number != -1:
        # module is already in chain and can be referenced by it's number

        _write_chain(file, path, depth, module.number)
        _pop(path)
        return

    if isinstance(module, ExternalModule) or not module.imports:
        # end of the branch

        _write_chain(file, path, depth)
    else:
        valid_chains = list()
        names = list()
        for imp in module.imports:
            # check if import is not duplicate and doesn't form cycle

            if isinstance(imp, ModuleImportUnit) and imp.module.full_name not in path \
                                                 and imp.module.full_name not in names:
                valid_chains.append(imp)
                names.append(imp.module.full_name)

        if len(valid_chains) == 0:
            # end of the branch
            _write_chain(file, path, depth)

        elif len(valid_chains) > 1:
            # branching the chain

            # set a reference number for a module before branching
            module.set_number()
            _write_chain(file, path, depth)
            file.write('\n')
            for imp in valid_chains:
                import_chain(imp.module, file, len(path), path)
            file.write('\n')
        else:
            module.set_number()
            import_chain(valid_chains[0].module, file, depth, path)

    _pop(path)


def _calculate_offset(path, depth=0):
    """Helper function to calculate chain branch offset when writing it to file"""

    offset = 0
    for index in range(depth):
        offset += len(path[index])
        if path[index] in discovered_modules and discovered_modules[path[index]].number != -1:
            offset += len(str(discovered_modules[path[index]].number))

    offset += 5 * (depth - 1)

    return offset


def _write_chain(file, path, depth=0, reference=None):
    """Write chain to file in a pretty way"""

    if depth != 0:
        offset = _calculate_offset(path, depth)
        file.write(offset * ' ' + ' --> ')

    for index in range(depth, len(path) - 1):
        if path[index] in discovered_modules and discovered_modules[path[index]].number != -1:
            file.write('[' + str(discovered_modules[path[index]].number) + '] ')
        file.write(path[index])
        file.write(' --> ')

    if path[-1] in discovered_modules and discovered_modules[path[-1]].number != -1:
        file.write('[' + str(discovered_modules[path[-1]].number) + '] ')
    file.write(path[-1])
    if reference is not None:
        file.write(' (watch ' + str(reference) + ')')
    elif path[-1] not in discovered_modules:
        file.write(' [ext]')
    elif discovered_modules[path[-1]].number == -1:
        file.write(' [end]')

    file.write('\n')


def _purge_numbers():
    """Delete reference integers of all discovered modules"""

    for m in discovered_modules.values():
        m.purge_number()

    module_units.next_number = -1


if __name__ == '__main__':
    main(sys.argv[1:])
