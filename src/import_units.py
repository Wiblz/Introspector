"""Classes representing imported names."""

from abc import ABC, abstractmethod

from src.module_units import ExternalModule, ModuleUnit
from src.util import _add


class ImportUnit(ABC):
    """Abstract base class for import units

    Contains some basic information about import unit
    """

    @abstractmethod
    def __init__(self, alias, module, inner, lineno):
        self.shadowed = False
        self.used = False
        self.alias = alias
        self.module = module
        self.inner = inner

        # line on which import statement was
        self.lineno = lineno


class FromImportUnit(ImportUnit):
    """Class representing 'from' imports

        'module':'Module' attribute represent module, from which names are imported.
        'item':'str' imported name.

    """

    def __init__(self, alias, item: 'str', module, lineno, inner=False):
        super().__init__(alias, module, inner, lineno)
        self.item = item

    # for inserting class objects in set
    def __hash__(self):
        return hash(self.module.full_name +
                    self.alias if self.alias is not None else '' +
                    self.item)

    def __str__(self):
        string = 'line ' + str(self.lineno) + ': '
        if self.alias is None:
            string += self.item + ' from ' + self.module.full_name + '. And was '
        else:
            string += self.item + ' as ' + self.alias + ' from ' + self.module.full_name + '. And was '

        if self.used:
            string += 'used.'
        else:
            string += 'not used.'

        return string

    def get_ref(self):
        """Get name by which imported name can be referenced in code."""
        return self.alias if self.alias is not None else self.item


class ModuleImportUnit(ImportUnit):
    """Class representing plain imports

        'module':'Module' attribute represent module, that is imported.

    """
    def __init__(self, alias, module, lineno, inner=False):
        super().__init__(alias, module, inner, lineno)
        self.names_used = list()

    # for inserting class objects in set
    def __hash__(self):
        return hash(self.module.full_name +
                    self.alias if self.alias is not None else '' +
                    str(self.names_used))

    def __str__(self):

        string = 'line ' + str(self.lineno) + ': ' + self.module.full_name
        if isinstance(self.module, ExternalModule):
            string += ' [External]'

        if self.alias is not None:
            string += ' as ' + self.alias

        string += self.get_usage()

        if self.used:
            string += ' But the module object was used.'

        return string

    def resolve_name_used(self, name):
        """Resolve referencing to an attribute of imported module.

        Check if referenced attribute is in imported module's namespace.
        If imported is external or name is not in it's namespace, then
        we assume that module object itself was used.
        """

        if isinstance(self.module, ExternalModule):
            _add(self.names_used, name)
            return

        exists = False
        for item in self.module.namespace:
            if name == item[0]:
                exists = True
                break

        if exists:
            _add(self.names_used, name)
        else:
            self.used = True

    def get_ref(self):
        """Get name by which imported module can be referenced in code."""
        return self.alias if self.alias is not None else self.module.name

    def get_usage(self):
        """Return string representing usage of names in imported module, primarily for writing to file."""
        return ' ' + str(len(self.names_used)) + ' out of ' \
                   + (str(len(self.module.namespace)) if isinstance(self.module, ModuleUnit) else '???') \
                   + ' names used.'
