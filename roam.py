class _RoamMissingItem:
    """ Falsey class used to flag item "missing" from traversal path """

    def __bool__(self):
        return False

    def __len__(self):
        return 0

    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration()

    def __str__(self):
        return "<Roam.MISSING>"


MISSING = _RoamMissingItem()


# By Alex Martelli from https://stackoverflow.com/a/952952/4970
# TODO Use `list(itertools.chain.from_iterable(l))` per comment on that link?
_flatten = lambda l: [item for sublist in l for item in sublist]


class Roamer:
    __is_multi_item = False

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
        elif attr_name == "__is_multi_item":
            return self.__is_multi_item

        # Stop here if no item to traverse
        if self.__item is MISSING:
            return self

        # Multi-item: `.xyz` => `[i.xyz for i in item]`
        if self.__is_multi_item:
            multi_items = []
            for i in self.__item:
                try:
                    multi_items.append(getattr(i, attr_name))
                except AttributeError:
                    try:
                        multi_items.append(i[attr_name])
                    except (TypeError, KeyError, IndexError):
                        pass
            self.__item = multi_items
            return self

        # Single item: `.xyz` => `item.xyz`
        try:
            self.__item = getattr(self.__item, attr_name)
            return self
        except AttributeError:
            pass

        # Fall back to `self.__getitem__()`
        return self[attr_name]

    def __getitem__(self, key_or_index_or_slice):
        # Stop here if no item to traverse
        if self.__item is MISSING:
            return self

        # Multi-item: `[xyz]` => `[i[xyz] for i in item]`
        # Single item: `[xyz]` => `item[xyz]`
        # import pdb; pdb.set_trace()  # TODO Delete this!
        if self.__is_multi_item:
            multi_items = []
            for i in self.__item:
                try:
                    multi_items.append(i[key_or_index_or_slice])
                except (TypeError, KeyError, IndexError):
                    pass
            self.__item = multi_items
        else:
            try:
                self.__item = self.__item[key_or_index_or_slice]
            except (TypeError, KeyError, IndexError):
                self.__item = MISSING  # Lookup failed

        # Flag the fact our item actually has multiple elements
        if isinstance(key_or_index_or_slice, slice):
            # Flatten item if we are are going deeper into nested multi-items
            if self.__is_multi_item:
                self.__item = _flatten(self.__item)
            self.__is_multi_item = True

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
        return bool(self.__item)

    def __str__(self):
        # TODO Report on path followed
        if self.__item is MISSING:
            return f"<Roamer: => {self.__item}>"
        return f"<Roamer: => {self.__item!r}>"


def r(item):
    return Roamer(item)
