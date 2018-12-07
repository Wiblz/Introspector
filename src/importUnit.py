from introspector import discovered_modules


class ImportUnit:
    def __init__(self, alias):
        self.used = False

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
        return "[" + \
               (self.module if isinstance(self.module, str) else self.module.full_name) + \
               (self.alias if hasattr(self, 'alias') else 'None') + \
               (self.members if hasattr(self, 'members') else 'None') + "]"

    def __repr__(self):
        return self.__str__()
