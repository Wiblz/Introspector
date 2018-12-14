from abc import ABC, abstractmethod
from pprint import pprint

from src.module import ExternalModule, ModuleUnit


class ImportUnit(ABC):
    @abstractmethod
    def __init__(self, alias, module, inner, lineno):
        self.shadowed = False
        self.used = False
        self.visited = False
        self.alias = alias
        self.module = module
        self.inner = inner
        self.lineno = lineno


class FromImportUnit(ImportUnit):
    def __init__(self, alias, item: 'str', module, lineno, inner=False):
        super().__init__(alias, module, inner, lineno)
        self.item = item

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
        return self.alias if self.alias is not None else self.item


class ModuleImportUnit(ImportUnit):
    def __init__(self, alias, module, lineno, inner=False):
        super().__init__(alias, module, inner, lineno)
        self.names_used = list()

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

        # for item in self.names_used:
        #     string += '\n\t' + item

        string += self.get_usage()

        if self.used:
            string += ' But the module object was used.'

        return string

    def resolve_name_used(self, name):
        if isinstance(self.module, ExternalModule):
            if name not in self.names_used:
                self.names_used.append(name)
            return

        exists = False
        for item in self.module.namespace:
            if name == item[0]:
                exists = True
                break

        if exists and name not in self.names_used:
            self.names_used.append(name)
        else:
            self.used = True

    def get_ref(self):
        return self.alias if self.alias is not None else self.module.name

    def get_usage(self):
        return ' ' + str(len(self.names_used)) + ' out of ' + (str(len(self.module.namespace))
                                                         if isinstance(self.module, ModuleUnit) else '???') + ' names used.'
