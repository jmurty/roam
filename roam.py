class _MissingItemSingleton:
    """ Falsey class used to flag item "missing" from traversal path """

    def __bool__(self):
        return False

    def __str__(self):
        return 'MISSING'


MISSING = _MissingItemSingleton()


class Roamer:

    def __init__(self, item):
        # TODO Handle `item` that is itself a `Roamer`
        self.__initial__item = self.__item = item

    def __getattr__(self, attr_name):
        # Stop here if no item to traverse
        if self.__item is MISSING:
            return self

        if attr_name[0] == '_':
            # `._123` => `item[123]`
            try:
                index = int(attr_name[1:])
            except ValueError:
                pass
            else:
                try:
                    self.__item = self.__item[index]
                    return self
                except (TypeError, IndexError):
                    pass

        # `.xyz` => `item.xyz`
        try:
            self.__item = getattr(self.__item, attr_name)
            return self
        except AttributeError:
            pass

        # `.xyz` => `item['xyz']`
        try:
            self.__item = self.__item[attr_name]
            return self
        except (TypeError, KeyError):
            pass

        # Lookup failed
        self.__item = MISSING
        return self

    def __getitem__(self, item):
        # Stop here if no item to traverse
        if self.__item is MISSING:
            return self

        # `[xyz]` => `item[xyz]`
        try:
            self.__item = self.__item[item]
            return self
        except (TypeError, KeyError, IndexError):
            pass

        # Lookup failed
        self.__item = MISSING
        return self

    def __call__(self, *args, _roam=False, **kwargs):
        # If item is callable: `.(x, y, z)` => `item(x, y, z)`
        if callable(self.__item):
            call_result = self.__item(*args, **kwargs)
        # If item is not callable: `.()` => return wrapped item
        # TODO What to do if we get extra arguments when unwrapping uncallable?
        else:
            call_result = self.__item

        if _roam:
            self.__item = call_result
            return self
        return call_result

    def __eq__(self, other):
        if isinstance(other, Roamer):
            return (
                    other.__initial__item == self.__initial__item
                    and other.__item == self.__item
            )
        return other == self.__item

    def __bool__(self):
        """ Return `False` if wrapped item is missing, else `bool(item)` """
        if self.__item is MISSING:
            return False
        return bool(self.__item)

    def __str__(self):
        # TODO Report on path followed
        if self.__item is MISSING:
            return f'<Roamer: => {self.__item}>'
        return f'<Roamer: => {self.__item!r}>'


def r(item):
    return Roamer(item)
