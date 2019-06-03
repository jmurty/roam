""" Easily traverse nested Python data structures """

__version__ = "0.1"

import re
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

    def __repr__(self):
        return "<Roam.MISSING>"


MISSING = _RoamMissingItem()

# From Alex Martelli in comment on https://stackoverflow.com/a/952952/4970
_flatten = lambda l: tuple(itertools.chain.from_iterable(l))


class _Path:
    _r_root_item_ = None
    _r_steps_ = []

    def __init__(self, initial_item, path_to_clone=None):
        if path_to_clone is not None:
            self._r_root_item_ = path_to_clone._r_root_item_
            self._r_steps_ = list(path_to_clone._r_steps_)  # Shallow copy list
        else:
            self._r_root_item_ = initial_item
            self._r_steps_ = []

    def log_getattr(self, attr_name, roamer):
        self._r_steps_.append((f".{attr_name}", roamer))

    def log_getitem(self, key_name, roamer):
        if isinstance(key_name, slice):
            item_desc = f"[{key_name.start or ''}:{key_name.stop or ''}{key_name.step and ':' + key_name.step or ''}]"
        else:
            item_desc = f"[{key_name!r}]"
        self._r_steps_.append((item_desc, roamer))

    def last_found(self):
        last_found_step = None, None, None
        for i, step in enumerate(self._r_steps_, 1):
            desc, roamer = step
            if roamer != MISSING:
                last_found_step = i, desc, roamer
        return last_found_step

    def first_missing(self):
        for i, step in enumerate(self._r_steps_, 1):
            desc, roamer = step
            if roamer == MISSING:
                return i, desc, roamer
        return None, None, None

    def description(self):
        result = []

        first_missing_index, first_missing_desc, first_missing_roamer = (
            self.first_missing()
        )
        if first_missing_index:
            result.append(
                f"missing step {first_missing_index} {first_missing_desc} for path "
            )

        result.append(f"<{type(self._r_root_item_).__name__}>")
        result += [desc for desc, _ in self._r_steps_]

        if first_missing_index:
            _, _, last_found_roamer = self.last_found()
            if last_found_roamer:
                result.append(f" at <{type(last_found_roamer()).__name__}>")

                # Generate hints
                last_found_data = last_found_roamer()
                if isinstance(last_found_data, (tuple, list)):
                    if re.match(r"\[\d+\]", first_missing_desc):
                        result.append(f" with length {len(last_found_data)}")
                else:
                    try:
                        keys = last_found_data.keys()
                        if keys:
                            result.append(
                                f" with keys [{', '.join([repr(k) for k in keys])}]"
                            )
                    except AttributeError:
                        attrs = dir(last_found_data)
                        if attrs and not isinstance(
                            last_found_data, (str, tuple, list)
                        ):
                            result.append(
                                f" with attrs [{', '.join([a for a in attrs if not a.startswith('_')])}]"
                            )

        return "".join(result)


class RoamPathException(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"<{type(self).__name__}: {self.path.description()}>"


class Roamer:
    # Internal state variables
    _r_item_ = None
    _r_path_ = None
    _r_is_multi_item_ = False
    # Options
    _r_raise_ = False
    # Temporary flags
    _r_via_alternate_lookup_ = False

    def __init__(self, item, _raise=False):
        # Handle `item` that is itself a `Roamer`
        if isinstance(item, Roamer):
            for attr in ("_r_item_", "_r_is_multi_item_", "_r_raise_"):
                setattr(self, attr, getattr(item, attr))
            self._r_path_ = _Path(item._r_item_, item._r_path_)
        else:
            self._r_item_ = item
            self._r_path_ = _Path(self._r_item_)
            self._r_raise_ = _raise

    def __getattr__(self, attr_name):
        # Stop here if no item to traverse
        if self._r_item_ is MISSING:
            if not self._r_via_alternate_lookup_:
                self._r_path_.log_getattr(attr_name, self)
            return self

        copy = Roamer(self)
        # Multi-item: `.xyz` => `(i.xyz for i in item)`
        if self._r_is_multi_item_:
            multi_items = []
            for i in self._r_item_:
                try:
                    multi_items.append(getattr(i, attr_name))
                except AttributeError:
                    try:
                        multi_items.append(i[attr_name])
                    except (TypeError, KeyError, IndexError):
                        pass
            copy._r_item_ = tuple(multi_items)
        # Single item: `.xyz` => `item.xyz`
        else:
            try:
                copy._r_item_ = getattr(copy._r_item_, attr_name)
            except AttributeError:
                # Attr lookup failed, no more attr lookup options
                copy._r_item_ = MISSING

        # Fall back to `self.__getitem__()` if lookup failed so far and we didn't come from there
        if copy._r_item_ is MISSING and not self._r_via_alternate_lookup_:
            try:
                self._r_via_alternate_lookup_ = True
                copy = self[attr_name]
            except RoamPathException:
                pass
            finally:
                copy._r_path_.log_getattr(attr_name, copy)
                self._r_via_alternate_lookup_ = False
        elif not self._r_via_alternate_lookup_:
            copy._r_path_.log_getattr(attr_name, copy)

        if copy._r_item_ is MISSING and copy._r_raise_:
            raise RoamPathException(copy._r_path_)

        return copy

    def __getitem__(self, key_or_index_or_slice):
        # Stop here if no item to traverse
        if self._r_item_ is MISSING:
            if not self._r_via_alternate_lookup_:
                self._r_path_.log_getitem(key_or_index_or_slice, self)
            return self

        copy = Roamer(self)
        # Multi-item: `[xyz]` => `(i[xyz] for i in item)`
        if self._r_is_multi_item_:
            multi_items = []
            for i in self._r_item_:
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
                    copy._r_item_ = multi_items[0]
                else:
                    copy._r_item_ = MISSING
            else:
                copy._r_item_ = tuple(multi_items)
        # Single item: `[xyz]` => `item[xyz]`
        else:
            try:
                copy._r_item_ = self._r_item_[key_or_index_or_slice]
            except (TypeError, KeyError, IndexError):
                # Index lookup failed, no more index lookup options
                copy._r_item_ = MISSING

        # Flag the fact our item actually has multiple elements
        if isinstance(key_or_index_or_slice, slice):
            # Flatten item if we are are going deeper into nested multi-items
            if copy._r_is_multi_item_:
                copy._r_item_ = _flatten(self._r_item_)
            copy._r_is_multi_item_ = True
        elif isinstance(key_or_index_or_slice, int):
            # No longer in a multi-item if we have selected a specific index item
            copy._r_is_multi_item_ = False

        # Fall back to `self.__getattr__()` if lookup failed so far and we didn't come from there
        if (
            copy._r_item_ is MISSING
            and not self._r_via_alternate_lookup_
            # Cannot do an integer attr lookup
            and not isinstance(key_or_index_or_slice, int)
        ):
            try:
                self._r_via_alternate_lookup_ = True
                copy = getattr(self, key_or_index_or_slice)
            except RoamPathException:
                pass
            finally:
                copy._r_path_.log_getitem(key_or_index_or_slice, copy)
                self._r_via_alternate_lookup_ = False
        elif not self._r_via_alternate_lookup_:
            copy._r_path_.log_getitem(key_or_index_or_slice, copy)

        if copy._r_item_ is MISSING and copy._r_raise_:
            raise RoamPathException(copy._r_path_)

        return copy

    def __call__(self, *args, _raise=False, _roam=False, _invoke=None, **kwargs):
        if _raise and self._r_item_ is MISSING:
            raise RoamPathException(self._r_path_)

        # If an explicit callable is provided, call `_invoke(item, x, y, z)`
        if _invoke is not None:
            call_result = _invoke(self._r_item_, *args, **kwargs)
        # If item is callable: `.(x, y, z)` => `item(x, y, z)`
        elif callable(self._r_item_):
            call_result = self._r_item_(*args, **kwargs)
        # If item is not callable: `.()` => return wrapped item unchanged
        # TODO What to do if we get extra arguments when unwrapping uncallable?
        else:
            call_result = self._r_item_

        # Re-wrap return as a `Roamer` if requested
        if _roam:
            copy = Roamer(self)
            copy._r_item_ = call_result
            return copy
        return call_result

    def __iter__(self):
        try:
            self._r_item__iter = iter(self._r_item_)
        except (AttributeError, TypeError):
            self._r_item__iter = None
        return self

    def __next__(self):
        if self._r_item__iter is None:
            raise StopIteration()
        next_value = next(self._r_item__iter)
        return Roamer(next_value)

    def __eq__(self, other):
        if isinstance(other, Roamer):
            return other._r_item_ == self._r_item_
        return other == self._r_item_

    def __bool__(self):
        return bool(self._r_item_)

    def __str__(self):
        if self._r_item_ is MISSING:
            return f"<Roamer: {self._r_path_.description()} => {self._r_item_}>"
        return f"<Roamer: {self._r_path_.description()} => {self._r_item_!r}>"


def r(item, _raise=False):
    return Roamer(item, _raise=_raise)


def r_strict(item):
    return Roamer(item, _raise=True)
