class _MissingItemSingleton:
    """ Falsey class used to flag item "missing" from traversal path """

    def __bool__(self):
        return False

    def __str__(self):
        return "MISSING"


MISSING = _MissingItemSingleton()


class Roamer:
    def __init__(self, item):
        # TODO Handle `item` that is itself a `Roamer`
        self.__initial__item = self.__item = item

    def __getattr__(self, attr_name):
        # Provide a way to get internal variable back again unmolested
        # TODO Find a cleaner way to do this
        if attr_name == "__item":
            return self.__item
        elif attr_name == "__initial_item":
            return self.__initial_item
        # Stop here if no item to traverse
        if self.__item is MISSING:
            return self

        if attr_name[0] == "_":
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

    def __call__(self, *args, _roam=False, _invoke=None, **kwargs):
        # If an explicit callable is provided, call `_invoke(item, x, y, z)`
        if _invoke is not None:
            call_result = _invoke(self.__item, *args, **kwargs)
        # If item is callable: `.(x, y, z)` => `item(x, y, z)`
        elif callable(self.__item):
            call_result = self.__item(*args, **kwargs)
        # If item is not callable: `.()` => return wrapped item unchanged
        # TODO What to do if we get extra arguments when unwrapping uncallable?
        else:
            call_result = self.__item

        # Re-wrap return as a `Roamer` if requested
        if _roam:
            self.__item = call_result
            return self
        return call_result

    def __iter__(self):
        try:
            self.__item_iter = self.__item.__iter__()
        except AttributeError:
            self.__item_iter = None
        return self

    def __next__(self):
        if self.__item_iter is None:
            raise StopIteration()
        next_value = self.__item_iter.__next__()
        item_roamer = Roamer(self)
        item_roamer.__item = next_value
        return item_roamer

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
            return f"<Roamer: => {self.__item}>"
        return f"<Roamer: => {self.__item!r}>"


def r(item):
    return Roamer(item)
