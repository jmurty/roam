class _MissingItemSingleton:
    """ Falsey class used to flag item "missing" from traversal path """

    def __bool__(self):
        return False


MISSING = _MissingItemSingleton()


class Roamer:

    def __init__(self, obj):
        # TODO Handle `obj` that is itself a `Roamer`
        self._initial_obj = self._obj = obj

    def __getattr__(self, attr_name):
        # Stop here if no object to traverse
        if self._obj is MISSING:
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
        if self._obj is MISSING:
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
        # If obj is callable: `.(x, y, z)` => `obj(x, y, z)`
        if callable(self._obj):
            return self._obj(*args, **kwargs)
        # If obj is not callable: `.()` => return wrapped object
        # TODO What to do if we get extra arguments when unwrapping uncallable?
        else:
            return self._obj

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
