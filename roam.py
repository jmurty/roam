""" Easily traverse nested Python data structures """

__version__ = "0.3.1"


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

    def __repr__(self):
        return "<MISSING>"


MISSING = _RoamMissingItem()


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

    def log_getattr(self, attr_name: str, roamer: "Roamer"):
        """
        Log the fact that a ``.dot`` attribute lookup was performed using a
        given name and the given ``Roamer`` shim was produced.
        """
        self._r_steps_.append((f".{attr_name}", unwrap(roamer)))

    def log_getitem(self, slice_value: slice, roamer: "Roamer"):
        """
        Log the fact that a ``["slice"]`` attribute lookup was performed using a
        given slice value and the given ``Roamer`` shim was produced.
        """
        if isinstance(slice_value, slice):
            item_desc = (
                f"[{slice_value.start or ''}:{slice_value.stop or ''}"
                f"{slice_value.step and ':' + slice_value.step or ''}]"
            )
        else:
            item_desc = f"[{slice_value!r}]"
        self._r_steps_.append((item_desc, unwrap(roamer)))

    def _last_found(self):
        last_found_step = None, None, self._r_root_item_
        for i, step in enumerate(self._r_steps_, 1):
            desc, data = step
            if data is not MISSING:
                last_found_step = i, desc, data
        return last_found_step

    def _first_missing(self):
        for i, step in enumerate(self._r_steps_, 1):
            desc, data = step
            if data is MISSING:
                return i, desc, data
        return None, None, self._r_root_item_

    def description(self) -> str:
        """
        Return a text description of this path, capturing:
        - the first step at which the path was invalid (if applicable)
        - the type of the root data object
        - path steps applied
        - hints about the type and content of data at the point the path became
          invalid (if applicable)
        """
        result = []

        first_missing_index, first_missing_desc, _ = self._first_missing()
        if first_missing_index:
            result.append(
                f"missing step {first_missing_index} {first_missing_desc} for path "
            )

        result.append(f"<{type(self._r_root_item_).__name__}>")
        result += [desc for desc, _ in self._r_steps_]

        if first_missing_index:
            _, _, last_found_data = self._last_found()
            if last_found_data is not MISSING:
                result.append(f" at <{type(last_found_data).__name__}>")

                # Generate hints
                if isinstance(last_found_data, (tuple, list, set, range)):
                    # Detect an integer key slice operation like `[3]` or `[-2]`
                    if first_missing_desc[0] == "[" and first_missing_desc[-1] == "]":
                        try:
                            int(first_missing_desc[1:-1])
                            result.append(f" with length {len(last_found_data)}")
                        except ValueError:
                            pass
                elif isinstance(
                    last_found_data, (str, int, float, complex, bool, bytes, bytearray)
                ):
                    pass  # No hint for primitive types
                elif last_found_data:
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

    def __eq__(self, other):
        if isinstance(other, _Path):
            return (
                self._r_root_item_ == other._r_root_item_
                and self._r_steps_ == other._r_steps_
            )
        return False


class RoamPathException(Exception):
    """
    An exception raised when a ``Roamer`` shim encounters an invalid path step
    if that shim has the ``_raise`` option set, or provided when returning data.

    The ``str()`` representation of this exception is a rich description of
    where your traversal path went wrong.
    """

    def __init__(self, path):
        super().__init__(self)
        self.path = path

    def __str__(self):
        return f"<RoamPathException: {self.path.description()}>"


class Roamer:
    """
    Act as a shim over your data objects, to intercept Python operations and do
    the extra work required to more easily traverse nested data.
    """

    # Internal state variables
    _r_item_ = None
    _r_path_ = None
    _r_is_multi_item_ = False
    # Options
    _r_raise_ = False
    # Temporary flags
    _r_via_alternate_lookup_ = False
    _r_item__iter = None

    def __init__(self, item, _raise=None):
        # Handle `item` that is itself a `Roamer`
        if isinstance(item, Roamer):
            for attr in ("_r_item_", "_r_is_multi_item_", "_r_raise_"):
                setattr(self, attr, getattr(item, attr))
            self._r_path_ = _Path(item._r_item_, item._r_path_)
        else:
            self._r_item_ = item
            self._r_path_ = _Path(self._r_item_)
        # Set or override raise flag if user provided a value
        if _raise is not None:
            self._r_raise_ = bool(_raise)

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
                lookup = None
                try:
                    lookup = getattr(i, attr_name)
                except (TypeError, AttributeError):
                    try:
                        lookup = i[attr_name]
                    except (TypeError, LookupError):
                        pass
                if isinstance(lookup, (tuple, list, range)):
                    multi_items += lookup
                elif lookup is not None:
                    multi_items.append(lookup)
            copy._r_item_ = tuple(multi_items)
        # Single item: `.xyz` => `item.xyz`
        else:
            try:
                copy._r_item_ = getattr(copy._r_item_, attr_name)
            except (TypeError, AttributeError):
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
        if copy._r_is_multi_item_ and not isinstance(key_or_index_or_slice, slice):
            # Flatten item if we have selected a specific integer index
            if isinstance(key_or_index_or_slice, int):
                try:
                    copy._r_item_ = copy._r_item_[key_or_index_or_slice]
                except (TypeError, LookupError):
                    copy._r_item_ = MISSING
                # No longer in a multi-item if we have selected a specific index item
                copy._r_is_multi_item_ = False
            # Otherwise apply slice lookup to each of multiple items
            else:
                multi_items = []
                for i in copy._r_item_:
                    lookup = None
                    try:
                        lookup = i[key_or_index_or_slice]
                    except (TypeError, LookupError):
                        try:
                            lookup = getattr(i, key_or_index_or_slice)
                        except (TypeError, AttributeError):
                            pass
                    if isinstance(lookup, (tuple, list, range)):
                        multi_items += lookup
                    elif lookup is not None:
                        multi_items.append(lookup)
                copy._r_item_ = tuple(multi_items)
        # Lookup for non-multi item data, or for slice lookups in all cases
        else:
            try:
                copy._r_item_ = copy._r_item_[key_or_index_or_slice]
            except (TypeError, LookupError):
                # Index lookup failed, no more index lookup options
                copy._r_item_ = MISSING

        # Flag the fact our item actually has multiple elements
        if isinstance(key_or_index_or_slice, slice):
            copy._r_is_multi_item_ = True

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
        # If item is not callable but we were given parameters, try to apply
        # them even though we know it won't work, to generate the appropriate
        # exception to let the user know their action failed
        elif args or kwargs:
            call_result = self._r_item_(*args, **kwargs)
        # If item is not callable: `.()` => return wrapped item unchanged
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
        except (TypeError, AttributeError):
            self._r_item__iter = None
        return self

    def __next__(self):
        if self._r_item__iter is None:
            raise StopIteration()
        next_value = next(self._r_item__iter)
        return Roamer(next_value)

    def __eq__(self, other):
        if isinstance(other, Roamer):
            for attr in ("_r_item_", "_r_path_", "_r_is_multi_item_", "_r_raise_"):
                if getattr(other, attr) != getattr(self, attr):
                    return False
            return True
        else:
            return other == self._r_item_

    def __bool__(self):
        return bool(self._r_item_)

    def __len__(self):
        try:
            return len(self._r_item_)
        except TypeError:
            # Here we know we have a non-MISSING item, but it doesn't support length lookups so
            # must be a single thing...
            # WARNING: This is black magic, does it make enough sense?
            return 1

    def __repr__(self):
        return f"<Roamer: {self._r_path_.description()} => {self._r_item_!r}>"


def r(item: object, _raise: bool = None) -> Roamer:
    """
    A shorter alias for constructing a ``Roamer`` shim class.
    """
    return Roamer(item, _raise=_raise)


def r_strict(item: object) -> Roamer:
    """
    A shorter alias for constructing a ``Roamer`` shim class in "strict" mode,
    which means that the ``_raise`` flag set so the shim will immediately raise
    a ``RoamPathException`` when you express an invalid path step.
    """
    return Roamer(item, _raise=True)


def unwrap(roamer: Roamer, _raise: bool = None) -> object:
    """
    Return the underlying data in the given ``Roamer`` shim object without
    the need to call that shim object.

    This is not the recommended way to get data from **roam** but you might
    prefer it, or it might help to solve unexpected bugs caused by the semi-
    magical call behaviour.
    """
    result = roamer._r_item_
    if _raise and result is MISSING:
        raise RoamPathException(roamer._r_path_)
    return result
