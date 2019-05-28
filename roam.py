import itertools


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

# From Alex Martelli in comment on https://stackoverflow.com/a/952952/4970
_flatten = lambda l: tuple(itertools.chain.from_iterable(l))


class _Path:
    _r_steps = []
    _r_has_missing = False

    def __init__(self, path_to_clone=None):
        if path_to_clone is not None:
            for attr in ("_r_steps", "_r_has_missing"):
                setattr(self, attr, getattr(path_to_clone, attr))
        else:
            self._r_steps = []
            self._r_has_missing = False

    def missing(self):
        if not self._r_has_missing:
            self._r_steps.append(" *!* ")
        self._r_has_missing = True

    def __getattr__(self, attr_name):
        self._r_steps.append(f".{attr_name}")

    def __getitem__(self, item):
        if isinstance(item, slice):
            # TODO Describe different slices
            item_desc = "[:]"
        else:
            item_desc = f"[{item!r}]"
        self._r_steps.append(item_desc)

    def steps_str(self):
        return "".join(self._r_steps)

    def __str__(self):
        return f"<roam.Path {self.steps_str()}>"


class RoamPathException(Exception):
    def __init__(self, path):
        self.path = path

    # TODO Improve path description in exception


class Roamer:
    # Internal state variables
    _r_item = None
    _r_initial_item = None
    _r_path = None
    _r_is_multi_item = False
    # Options
    _r_raise = False
    # Temporary flags
    _r_skip_path_updates = False

    def __init__(self, item, _raise=False):
        # Handle `item` that is itself a `Roamer`
        if isinstance(item, Roamer):
            for attr in ("_r_item", "_r_initial_item", "_r_is_multi_item", "_r_raise"):
                setattr(self, attr, getattr(item, attr))
            self._r_path = _Path(item._r_path)
        else:
            self._r_initial_item = self._r_item = item
            self._r_path = _Path()
            self._r_raise = _raise

    def __getattr__(self, attr_name):
        # Stop here if no item to traverse
        if self._r_item is MISSING:
            getattr(self._r_path, attr_name)
            return self

        # Multi-item: `.xyz` => `(i.xyz for i in item)`
        if self._r_is_multi_item:
            multi_items = []
            for i in self._r_item:
                try:
                    multi_items.append(getattr(i, attr_name))
                except AttributeError:
                    try:
                        multi_items.append(i[attr_name])
                    except (TypeError, KeyError, IndexError):
                        pass
            copy = Roamer(self)
            copy._r_item = tuple(multi_items)
            getattr(copy._r_path, attr_name)
            return copy

        # Single item: `.xyz` => `item.xyz`
        try:
            copy = Roamer(self)
            copy._r_item = getattr(copy._r_item, attr_name)
            return copy
        except AttributeError:
            pass

        # Fall back to `self.__getitem__()`
        try:
            self._r_skip_path_updates = True
            copy = self[attr_name]
            self._r_skip_path_updates = False
        except RoamPathException:
            raise
        finally:
            # Log attribute lookup to path, successful or not
            getattr(copy._r_path, attr_name)

        return copy

    def __getitem__(self, key_or_index_or_slice):
        # Stop here if no item to traverse
        if self._r_item is MISSING:
            if not self._r_skip_path_updates:
                self._r_path[key_or_index_or_slice]
            return self

        # Multi-item: `[xyz]` => `(i[xyz] for i in item)`
        # Single item: `[xyz]` => `item[xyz]`
        copy = Roamer(self)
        if self._r_is_multi_item:
            multi_items = []
            for i in self._r_item:
                try:
                    multi_items.append(i[key_or_index_or_slice])
                except (TypeError, KeyError, IndexError):
                    pass
            copy._r_item = tuple(multi_items)
        else:
            try:
                copy._r_item = self._r_item[key_or_index_or_slice]
            except (TypeError, KeyError, IndexError):
                # Key lookup failed, which is also the last possible lookup
                copy._r_item = MISSING
                copy._r_path.missing()

        # Flag the fact our item actually has multiple elements
        if isinstance(key_or_index_or_slice, slice):
            # Flatten item if we are are going deeper into nested multi-items
            if copy._r_is_multi_item:
                copy._r_item = _flatten(self._r_item)
            copy._r_is_multi_item = True

        # Log attribute lookup to path, successful or not
        if not self._r_skip_path_updates:
            copy._r_path[key_or_index_or_slice]

        if copy._r_item is MISSING and copy._r_raise:
            raise RoamPathException(copy._r_path)

        return copy

    def __call__(self, *args, _raise=False, _roam=False, _invoke=None, **kwargs):
        if _raise and self._r_item is MISSING:
            raise RoamPathException(self._r_path)

        # If an explicit callable is provided, call `_invoke(item, x, y, z)`
        if _invoke is not None:
            call_result = _invoke(self._r_item, *args, **kwargs)
        # If item is callable: `.(x, y, z)` => `item(x, y, z)`
        elif callable(self._r_item):
            call_result = self._r_item(*args, **kwargs)
        # If item is not callable: `.()` => return wrapped item unchanged
        # TODO What to do if we get extra arguments when unwrapping uncallable?
        else:
            call_result = self._r_item

        # Re-wrap return as a `Roamer` if requested
        if _roam:
            copy = Roamer(self)
            copy._r_item = call_result
            return copy
        return call_result

    def __iter__(self):
        try:
            self._r_item_iter = iter(self._r_item)
        except (AttributeError, TypeError):
            self._r_item_iter = None
        return self

    def __next__(self):
        if self._r_item_iter is None:
            raise StopIteration()
        next_value = next(self._r_item_iter)
        return Roamer(next_value)

    def __eq__(self, other):
        if isinstance(other, Roamer):
            return other._r_item == self._r_item
        return other == self._r_item

    def __bool__(self):
        return bool(self._r_item)

    def __str__(self):
        if self._r_item is MISSING:
            return f"<Roamer: {type(self._r_initial_item)}{self._r_path.steps_str()} => {self._r_item}>"
        return f"<Roamer: {type(self._r_initial_item)}{self._r_path.steps_str()} => {self._r_item!r}>"


def r(item, _raise=False):
    return Roamer(item, _raise=_raise)


def r_strict(item):
    return Roamer(item, _raise=True)
