"""Utility functions for the Introspector."""
import ast


def _add(list, item):
    """Add an element to list if it is not already there"""
    if item not in list:
        list.append(item)


def _pop(list):
    """Pop an element from the list if it is not empty.

    This is a helper function for safe item popping from the list

    """
    if list:
        return list.pop()


def _get_ast(module: 'ModuleUnit'):
    """Get an abstract syntax tree for module"""

    with open(module.path + module.name + '.py') as f:
        a = f.read()

    return ast.parse(a)


def resolve_relative_import(current_name, imported_name, level):
    """Resolves relative imports, returning full name of the imported module.

    :param current_name: full name of the module, inside of which import occurs.
    :param imported_name: name of module being imported
    :param level: level of relative import (where . means level 1)
    :return: full name of imported module
    """
    if level == 0:
        return imported_name
    else:
        index = 0
        for index, char in reversed(list(enumerate(current_name))):
            if char == '.':
                level -= 1
                if level == 0: break

        if index == 0:
            return imported_name
        else:
            return current_name[0:index+1] + imported_name
