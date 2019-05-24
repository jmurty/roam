class _MissingItemSingleton:
    """ Falsey class used to flag item "missing" from traversal path """

    def __bool__(self):
        return False


class _FoundItemSingleton:
    """ Truthy class used to flag item "found" with traversal path """

    def __bool__(self):
        return True


MISSING = _MissingItemSingleton()


FOUND = _FoundItemSingleton()


class Roamer:

    def __init__(self, obj):
        # TODO Handle `obj` that is itself a `Roamer`
        self._initial_obj = self._obj = obj

    @property
    def MISSING(self):
        return self._obj is MISSING

    @property
    def FOUND(self):
        return self._obj is not MISSING

    def __getattr__(self, attr_name):
        # `._` => return wrapped object
        if attr_name == '_':
            return self._obj

        # Stop here if no object to traverse
        if self.MISSING:
            return self

        if attr_name[0] == '_':
            # `._123` => `obj[123]`
            try:
                index = int(attr_name[1:])
            except ValueError:
                pass
            else:
                try:
                    self._obj = self._obj[index]
                    return self
                except (TypeError, IndexError):
                    pass

        # `.xyz` => `obj.xyz`
        try:
            self._obj = getattr(self._obj, attr_name)
            return self
        except AttributeError:
            pass

        # `.xyz` => `obj['xyz']`
        try:
            self._obj = self._obj[attr_name]
            return self
        except (TypeError, KeyError):
            pass

        # Lookup failed
        self._obj = MISSING
        return self

    def __getitem__(self, item):
        # Stop here if no object to traverse
        if self.MISSING:
            return self

        # `[xyz]` => `obj[xyz]`
        try:
            self._obj = self._obj[item]
            return self
        except (TypeError, KeyError, IndexError):
            pass

        # Lookup failed
        self._obj = MISSING
        return self

    def __call__(self, *args, **kwargs):
        # Stop here if no object to traverse
        if self.MISSING:
            return self

        # `(x, y, z)` => `obj(x, y, z)`
        try:
            self._obj = self._obj(*args, **kwargs)
            return self
        except TypeError:
            pass

        # Call failed
        self._obj = MISSING
        return self

    def __eq__(self, other):
        if isinstance(other, Roamer):
            return (
                    other._initial_obj == self._initial_obj
                    and other._obj == self._obj
            )
        return other == self._obj

    def __bool__(self):
        """ Return `False` if wrapped object is missing, else `bool(obj)` """
        if self._obj is MISSING:
            return False
        return bool(self._obj)

    def __str__(self):
        # TODO Report on path followed
        return f'<Roamer: => {self._obj!r}>'


def r(obj):
    return Roamer(obj)
