import importlib
import inspect
import pkgutil
from pprint import pprint


# path = r"/home/counterfeit/Projects/Introspector/"
path = r"/usr/lib/python3.6/"
# path = r"/usr/lib/python3.6/"
# path = r"/home/counterfeit/.IntelliJIdea2018.2/config/plugins/python/helpers/typeshed/stdlib/2and3/"
importlib.errors = 0
importlib.success = 0


def list_modules(packages=[], offset=0):
    packages_string = '.'.join(packages)
    path_string = '/'.join(packages)
    error = False
    print('\t' * (offset - 1), packages_string, sep='')
    for i in pkgutil.iter_modules([path + path_string]):
        if i.name == "__main__":
            continue
        if i.ispkg:
            packages.append(i.name)
            list_modules(packages, offset + 1)
        else:
            try:
                if packages_string:
                    print('\t' * offset, packages_string, ".", i.name, sep='')
                    imported_module = importlib.import_module('.' + i.name, package=packages_string)
                else:
                    print('\t' * offset, i.name, sep='')
                    imported_module = importlib.import_module(i.name)
                pprint(inspect.getmembers(imported_module))
            except:
                print("\t" * offset, "[ERROR IMPORTING] ", packages_string, ".", i.name, sep='')
                error = True

            if error:
                importlib.errors += 1
            else:
                importlib.success += 1
            error = False
            # print(imported_module)

    _pop(packages)


def main():
    # list_modules()
    # print(importlib.success, importlib.errors)

    imported_module = importlib.import_module('functools')
    a = inspect.getmembers(imported_module)
    a = [x for x in a if x[0] != '__builtins__']
    pprint(a)


def _pop(l):
    if l:
        l.pop()


if __name__ == '__main__':
    main()
