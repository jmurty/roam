# roam – Easily traverse nested Python data structures

**roam** provides an API to easily traverse nested data structures with plain Python syntax and without annoying error-handling. 

[![Latest Version](https://img.shields.io/pypi/v/roam.svg)](https://pypi.org/project/roam/)
[![License](https://img.shields.io/github/license/jmurty/roam.svg)](https://pypi.org/project/roam/)
[![Python Versions Supported](https://img.shields.io/pypi/pyversions/roam.svg)](https://pypi.org/project/roam/)
[![Build Status](https://travis-ci.org/jmurty/roam.svg?branch=master)](https://travis-ci.org/jmurty/roam)
[![Black code style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

Three steps to use **roam**:

1. Wrap your data in a `Roamer` shim
2. Express a path to traverse through your data with `.dot` or `["slice"]` notation, as you prefer
3. Get the result by *calling* the `Roamer` shim object like a function.

```python
# Example nested data: nested dicts and a class with attributes
>>> import collections
>>> Point = collections.namedtuple('Point', ['x', 'y'])
>>> data = {"a": {"b": {"c": Point(x=100, y=200)}}}

# 1. Wrap your data in a Roamer shim
>>> import roam
>>> roamer = roam.Roamer(data)

# 2. Express a path to traverse
>>> step = roamer.a.b.c.x

# 3. Get the result by calling the Roamer shim
>>> step()
100

# And here is a more terse example (read on for details)
>>> roam.r(data).a.b.c['y']()
200

```


## Installation

[Install **roam**](https://pypi.org/project/roam/) with pip:

```bash
$ pip install roam
``` 

**roam** works with Python versions 3.6 and later and has no dependencies.


## Basics

### The `Roamer` shim

**roam** works by providing the `Roamer` class to serve as a shim over your data objects, to intercept Python operations and do the extra work required to more easily traverse nested data.

Make a shim for your data by calling `roam.Roamer(data)` or you can use the shorter `r` alias function: `roam.r(data)`

### Express a path to traverse

Traverse your data by expressing the path to follow in Python `.dot` attribute or key/index `["slice"]` operations.

As you add each operation to the path expression, **roam** returns a new `Roamer` shim representing the data at that point in the path and the steps taken to get there.

Because **roam** intercepts and interprets path traversal operations it can provide some nice features like:

- use dot syntax – less typing – even if the underlying data doesn't support it:

  ```python
  # .name instead of ["name"]
  >>> roam.r({"name": "value"}).name()
  'value'

  ```

- or use slice syntax if you prefer. **roam** makes dot or slice operations work regardless of the underlying objects:

  ```python
  # ["x"] instead of .x
  >>> roam.r(Point(x=100, y=200))["x"]()
  100

  ```

- in fact, mix and match dot and slice to your heart's content:

  ```python
  # Dots for slices and slices for dots!
  >>> roam.r({"point": Point(x=100, y=200)}).point["y"]()
  200

  ```

- *but* you must use slice syntax to traverse a path step that is [not a valid Python variable name](https://www.python.org/dev/peps/pep-0008/#prescriptive-naming-conventions):

  ```python
  # .no-dash-in-attrs is not a legal Python variable name
  >>> roam.r({"no-dash-in-attrs": "thanks"})["no-dash-in-attrs"]()
  'thanks'

  ```

In some situations your choice of dot or slice notation in a path can matter: when your data has both an attribute and a key with the same name. Because **roam** applies your expressed operation first, you can make sure the right operation is applied:

```python
# Data with ambiguous "items" name: keyword in dict, and built in method
>>> roamer = roam.r({"items": [1, 2, 3]})

# A dot lookup returns the dict method, which probably isn't what you want...
>>> roamer.items()
dict_items([('items', [1, 2, 3])])

# ...so use a slice lookup instead. Roam will do the slice lookup first
>>> roamer["items"]()
[1, 2, 3]

```

### Get a result, or `MISSING`

You get a final result by *calling* the shim `Roamer` object like a function with `()` parentheses, which tells **roam** to return the underlying data.

If you expressed a valid path through your data, you will get the result you expect.

If you expressed an *invalid* path, **roam** will *not* complain or raise an exception. Instead, it will return a `roam.MISSING` marker object to let you know that there was no data available at the path.

You can check for the `roam.MISSING` marker object directly if you want, but this marker is "falsey" in a number of ways which also makes it easy to act on a missing result without explicitly checking for one:

```python
>>> roamer = roam.r(Point(x=100, y=200))

# Check for the `roam.MISSING` object directly
>>> result = roamer.z()
>>> result is roam.MISSING
True

# Example falsey behaviour
>>> bool(result)
False
>>> len(result)
0
>>> [i for i in result]
[]

# This falsey behaviour makes it easy to fall back to a default
>>> roamer.x() or "My fallback"
100
>>> roamer.z() or "My fallback"
'My fallback'

```

Of course, sometimes it may be better for your path traversal to fail very explicitly by raising an exception. Use the `_raise` argument when calling the shim to trigger a rich `RoamPathException` instead of returning a `roam.MISSING` object:
```python
>>> try:
...     roamer.x.y.z(_raise=True)
... except roam.RoamPathException as ex:
...     str(ex)
'<RoamPathException: missing step 2 .y for path <Point>.x.y.z at <int>>'

```

### Traverse collections

If your data includes collections of items such as a `list`, you can tell **roam** to iterate over the collection and apply following path lookups to *each item* in the collection instead of the collection as a whole.

You do this with a standard slice operation that would return a collection in standard Python usage. Use the special `[:]` slice to iterate over all items in the collection, or a subset slice such as `[2:3]` to iterate over a subset.

When you traverse a collection with a slice operation, **roam** will:

- iterate over each item in the collection
- flatten the results at each step in the following path, avoiding nested collections
- *filter out* data items that don't match the following path.  
  Within collections, invalid paths are ignored instead of returning `roam.MISSING` marker objects
- return a final `tuple` of matching data items.

Some examples:
```python
>>> roamer = roam.r({
...     "people": [
...         {"name": "Alice", "age": 34},
...         {"name": "Bob", "age": 42},
...         {"name": "Trudy"},  # Unknown age
...     ]
... })

# A `list` object does not have the attribute "name"
>>> roamer.people.name()
<Roam.MISSING>

# Use the "all items" [:] slice operation to iterate over item in `people`
>>> roamer.people[:].name()
('Alice', 'Bob', 'Trudy')

# Get all but the last person's name
>>> roamer.people[:-1].name()
('Alice', 'Bob')

# Alice is 34, Bob is 42. Trudy has no "age" data so has no result
>>> roamer.people[:].age()
(34, 42)

```

When traversing a collection, if you use an integer index lookup instead of a slice **roam** will return the single n*th* item from the collection as you would expect:

```python
# Get just the last people item
>>> roamer.people[-1].name()
'Trudy'

```

**WARNING**: **roam** has only rudimentary support for traversing nested collections: it always flattens the data. This should be fine for simple situations, but if you need to traverse non-trivial collections data and return nested collections you should either do this work with `for` loops in Python code or try the related project [glom](#related-projects) as an alternative.

```python
# Double nested collections: "people" then "pets"
>>> roamer = roam.r({
...     "people": [
...         {"name": "Alice", 
...          "pets": [
...             {"type": "cat", "name": "Mog"},
...             {"type": "dog", "name": "Spot"},
...         ]},
...         {"name": "Bob",
...          "pets": [
...             {"type": "budgie", "name": "Bertie"},
...         ]},
...     ]
... })

# Get flattened name results from the "people" > "pets" nested collection
>>> roamer.people[:].pets.name()
('Mog', 'Spot', 'Bertie')

# Get just the n-th result at at a given level
>>> roamer.people[:].pets.name[0]()
'Mog'

```


## Advanced

**TODO**

- falsey-ness of `roam.MISSING`
- rich path descriptions and exceptions
- **roam** is a shim (lookup order, equality, iteration, falsey-ness, truthiness, length)
- call nested methods
- re-wrap result of nested method call with the `_roam` option
- fail fast with the `_raise` option
- call arbitrary functions with the `_invoke` option


## Related projects

These similar tools and libraries inspired and informed **roam**:

- [glom](https://glom.readthedocs.io/) – *Restructuring data, the Python way.*  
  This library's data access and [glom.T](https://glom.readthedocs.io/en/latest/api.html#glom.T) components do everything **roam** does and more, while **roam** aims to be smaller and simpler. If you find **roam** too limiting, **glom** is the library you want.
- The Django template language's [variable dot lookup](https://docs.djangoproject.com/en/2.2/ref/templates/language/#variables) gave us a taste for dot-path data traversal in the first place.
- [jmespath](https://pypi.org/project/jmespath/) – *JMESPath (pronounced “james path”) allows you to declaratively specify how to extract elements from a JSON document.*
- [traversify](https://pypi.org/project/traversify/) – *Handy python classes for manipulating json data, providing syntactic sugar for less verbose, easier to write code.*


## Contributing

- Contributors must follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md)
- Code contributions must be formatted with Black for consistency
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black) 


## License
 
 **roam** is licensed under Apache, Version 2.0

```text
Copyright 2019 James Murty

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
