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
    _r_initial_item = None
    _r_steps = []

    def __init__(self, initial_item, path_to_clone=None):
        if path_to_clone is not None:
            for attr in ("_r_initial_item", "_r_steps"):
                setattr(self, attr, getattr(path_to_clone, attr))
        else:
            self._r_initial_item = initial_item
            self._r_steps = []

    def log_getattr(self, attr_name, value):
        self._r_steps.append((f".{attr_name}", value, value is MISSING))

    def log_getitem(self, key_name, value):
        if isinstance(key_name, slice):
            item_desc = f"[{key_name.start or ''}:{key_name.stop or ''}{key_name.step and ':' + key_name.step or ''}]"
        else:
            item_desc = f"[{key_name!r}]"
        self._r_steps.append((item_desc, value, value is MISSING))

    def last_found(self):
        last_found_step = None, None
        for i, step in enumerate(self._r_steps, 1):
            if not step[2]:
                last_found_step = i, step
        return last_found_step

    def first_missing(self):
        for i, step in enumerate(self._r_steps, 1):
            if step[2]:
                return i, step
        return None, None

    def description(self):
        result = []

        first_missing_index, first_missing_step = self.first_missing()
        if first_missing_step:
            desc, _, _ = first_missing_step
            result.append(f"missing step {first_missing_index} {desc} for path ")

        result.append(f"<{type(self._r_initial_item).__name__}>")
        result += [desc for desc, _, _ in self._r_steps]

        if first_missing_step:
            _, last_found_step = self.last_found()
            if last_found_step:
                result.append(f" at <{type(last_found_step[1]).__name__}>")

        return "".join(result)


class RoamPathException(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"<{type(self).__name__}: {self.path.description()}>"


class Roamer:
    # Internal state variables
    _r_item = None
    _r_initial_item = None
    _r_path = None
    _r_is_multi_item = False
    # Options
    _r_raise = False
    # Temporary flags
    _r_via_alternate_lookup = False

    def __init__(self, item, _raise=False):
        # Handle `item` that is itself a `Roamer`
        if isinstance(item, Roamer):
            for attr in ("_r_item", "_r_initial_item", "_r_is_multi_item", "_r_raise"):
                setattr(self, attr, getattr(item, attr))
            self._r_path = _Path(item._r_initial_item, item._r_path)
        else:
            self._r_initial_item = self._r_item = item
            self._r_path = _Path(self._r_initial_item)
            self._r_raise = _raise

    def __getattr__(self, attr_name):
        # Stop here if no item to traverse
        if self._r_item is MISSING:
            if not self._r_via_alternate_lookup:
                self._r_path.log_getattr(attr_name, MISSING)
            return self

        copy = Roamer(self)
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
            copy._r_item = tuple(multi_items)
        # Single item: `.xyz` => `item.xyz`
        else:
            try:
                copy._r_item = getattr(copy._r_item, attr_name)
            except AttributeError:
                # Attr lookup failed, no more attr lookup options
                copy._r_item = MISSING

        # Fall back to `self.__getitem__()` if lookup failed so far and we didn't come from there
        if copy._r_item is MISSING and not self._r_via_alternate_lookup:
            try:
                self._r_via_alternate_lookup = True
                copy = self[attr_name]
            finally:
                copy._r_path.log_getattr(attr_name, copy._r_item)
                self._r_via_alternate_lookup = False
        elif not self._r_via_alternate_lookup:
            copy._r_path.log_getattr(attr_name, copy._r_item)

        if copy._r_item is MISSING and copy._r_raise:
            raise RoamPathException(copy._r_path)

        return copy

    def __getitem__(self, key_or_index_or_slice):
        # Stop here if no item to traverse
        if self._r_item is MISSING:
            if not self._r_via_alternate_lookup:
                self._r_path.log_getitem(key_or_index_or_slice, MISSING)
            return self

        copy = Roamer(self)
        # Multi-item: `[xyz]` => `(i[xyz] for i in item)`
        if self._r_is_multi_item:
            multi_items = []
            for i in self._r_item:
                try:
                    multi_items.append(i[key_or_index_or_slice])
                except (TypeError, KeyError, IndexError):
                    try:
                        multi_items.append(getattr(i, key_or_index_or_slice))
                    except (TypeError, AttributeError):
                        pass
            if isinstance(key_or_index_or_slice, int):
                # Flatten item if we have selected a specific index item
                if multi_items:
                    copy._r_item = multi_items[0]
                else:
                    copy._r_item = MISSING
            else:
                copy._r_item = tuple(multi_items)
        # Single item: `[xyz]` => `item[xyz]`
        else:
            try:
                copy._r_item = self._r_item[key_or_index_or_slice]
            except (TypeError, KeyError, IndexError):
                # Index lookup failed, no more index lookup options
                copy._r_item = MISSING

        # Flag the fact our item actually has multiple elements
        if isinstance(key_or_index_or_slice, slice):
            # Flatten item if we are are going deeper into nested multi-items
            if copy._r_is_multi_item:
                copy._r_item = _flatten(self._r_item)
            copy._r_is_multi_item = True
        elif isinstance(key_or_index_or_slice, int):
            # No longer in a multi-item if we have selected a specific index item
            copy._r_is_multi_item = False

        # Fall back to `self.__getattr__()` if lookup failed so far and we didn't come from there
        if (
            copy._r_item is MISSING
            and not self._r_via_alternate_lookup
            # Cannot do an integer attr lookup
            and not isinstance(key_or_index_or_slice, int)
        ):
            try:
                self._r_via_alternate_lookup = True
                copy = getattr(self, key_or_index_or_slice)
            finally:
                copy._r_path.log_getitem(key_or_index_or_slice, copy._r_item)
                self._r_via_alternate_lookup = False
        elif not self._r_via_alternate_lookup:
            copy._r_path.log_getitem(key_or_index_or_slice, copy._r_item)

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
            return f"<Roamer: {self._r_path.description()} => {self._r_item}>"
        return f"<Roamer: {self._r_path.description()} => {self._r_item!r}>"


def r(item, _raise=False):
    return Roamer(item, _raise=_raise)


def r_strict(item):
    return Roamer(item, _raise=True)
