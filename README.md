# roam – Easily traverse nested Python data structures

**roam** provides an API to more easily traverse nested data structures using standard Python syntax without pesky error-handling at each step. 

[![Build Status](https://travis-ci.org/jmurty/roam.svg?branch=master)](https://travis-ci.org/jmurty/roam)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

There are three simple steps to use **roam**:

1. Wrap your data in a `Roamer` shim
2. Express the path or paths to traverse through your data with "dot" or "slice" notation, whichever you prefer
3. Get the result by *calling* the `Roamer` shim object like a function.

```python
# Example nested data: nested dicts and class with attributes
>>> import collections
>>> Point = collections.namedtuple('Point', ['x', 'y'])
>>> data = {"a": {"b": {"c": Point(100, 200)}}}

# 1. Wrap your data in a Roamer shim
>>> import roam
>>> roamer = roam.Roamer(data)

# 2. Express path to traverse
>>> step = roamer.a.b.c.x

# 3. Get result by calling the Roamer shim
>>> step()
100

# Put it all together slightly differently (read on for details)
>>> roam.r(data).a.b.c['y']()
200

```


## Installation

Install **roam** with pip:

```bash
$ pip install roam
``` 

**roam** works with Python versions 3.6 and later and has no dependencies.


## Basics

### `Roamer` shim

**roam** works by providing the `Roamer` class as a shim over your data objects, to intercepts Python operations and do some extra work to make it easier to traverse nested data.

Get a shim object over your data by calling `roam.Roamer(data)` or you can use the shorter `r` alias: `roam.r(data)`

### Traverse paths

You traverse your data within the **roam** shim by expressing the path (or paths) to follow in Python attribute (dot) or key/index (slice) syntax.

At each step you express in a path, **roam** returns a new `Roamer` shim that represents data at that point in the path and the steps taken up to there.

Because **roam** intercepts and interprets the path operations it can provide some nice features:

- use dot syntax whether the data item supports attribute or index lookups:

  ```python
  >>> roam.r({"key": "value"}).key()
  'value'

  ```

- use slice syntax if you prefer, **roam** makes dot or slice operations work regardless of the underlying objects:

  ```python
  >>> roam.r(Point(x=1, y=2))["x"]()
  1

  ```

- mix and match dot and slice to your heart's content:

  ```python
  >>> roam.r({"point": Point(x=1, y=2)}).point["y"]()
  2

  ```

- use slice syntax to traverse a path step that cannot be a valid Python attribute name:  

  ```python
  >>> roam.r({"no-dash-in-attrs": "thanks"})["no-dash-in-attrs"]()
  'thanks'

  ```

Generally it makes no difference whether you choose dot or slice syntax to traverse a path, but in cases where an attribute and a key have the same name the choice can matter. Because **roam** applies your chosen operation first, you can handle this situation by telling it what to do:

```python
# Data with ambiguous "items" name: keyword in dict, and dict method
>>> roamer = roam.r({"items": [1, 2, 3]})

# A dot lookup returns the dict method, which probably isn't what you want...
>>> roamer.items()
dict_items([('items', [1, 2, 3])])

# ...so use a slice lookup instead. Roam will then do a slice lookup first
>>> roamer["items"]()
[1, 2, 3]

```

### Get a result, or `MISSING`

You get a final result by *calling* the shim `Roamer` object like a function with `()` parentheses, to tell **roam** to return the underlying data from behind the shim.

If you expressed a valid path through your data you will get the result you expect.

If you expressed an **invalid** path, **roam** will *not* complain or raise an exception. Instead, it will return a `roam.MISSING` marker object to let you know that there is no data available at the path.

The `roam.MISSING` object is falsey in a number of ways, so you can either check for an invalid "missing" result directly or rely on its falsey behaviour:

```python
>>> roamer = roam.r(Point(x=1, y=2))

# Check for the `roam.MISSING` object directly
>>> roamer.z() is roam.MISSING
True

# Check indirectly via falsey behaviour
>>> bool(roamer.z())
False
>>> len(roamer.z())
0
>>> [i for i in roamer.z()]
[]

# The falsey MISSING object makes it easy to fall back to a default
>>> roamer.x() or "My fallback"
1
>>> roamer.z() or "My fallback"
'My fallback'

```

Of course, sometimes it's better to fail very clearly with an exception. Use the `_raise` argument to trigger a rich `RoamPathException` instead of returning a `roam.MISSING` object:
```python
>>> try:
...     roamer.x.y.z(_raise=True)
... except roam.RoamPathException as ex:
...     str(ex)
'<RoamPathException: missing step 2 .y for path <Point>.x.y.z at <int>>'

```

### Traverse collections

If your data includes collections of items such as a `list`, you can tell **roam** to iterate over the collection and apply following path lookups to **each item** in the collection instead of the collection as a whole.

You do this with a standard slice operation that *would return a collection* in standard Python usage. Use the special `[:]` slice to iterate over all items in the collection, or a subset slice using `[2:3]` etc to iterate over a subset.

When you traverse a collection with a slice operation, the final result is a `tuple` of data items.

For example:
```python
>>> roamer = roam.r({
...     "people": [
...         {"name": "Alice", "age": 34},
...         {"name": "Bob", "age": 42},
...         {"name": "Trudy"},  # Unknown age
...     ]
... })

# A `list` object does not have the attributee `name`
>>> roamer.people.name()
<Roam.MISSING>

# Use the "all items" [:] slice operation to iterate over each item
>>> roamer.people[:].name()
('Alice', 'Bob', 'Trudy')

# Get all but the last person names
>>> roamer.people[:-1].name()
('Alice', 'Bob')

```

**roam** handles collections differently from single items in the path in that it **ignores** items where the following path is invalid, filtering them out instead of returning `roam.MISSING` marker objects.

You can think of a collection traversal in **roam** as being like a combined *for-each* and *filter*.

```python
# Alice is 34, Bob is 42, Trudy has no "age" data
>>> roamer.people[:].age()
(34, 42)

```

When traversing a collection, if you use an integer index lookup instead of a slice **roam** will return the single n*th* item from the collection as you would expect:

```python
>>> roamer.people[-1].name()
'Trudy'

```

**WARNING**: **roam** has only *rudimentary* support for traversing nested collections. Simple cases should work, but if you need to traverse non-trivial collections data you should do the work with `for` loops in your code.

```python
>>> roamer = roam.r({
...     "people": [
...         {"name": "Alice", "pets": [
...             {"type": "cat", "name": "Mog"},
...             {"type": "dog", "name": "Spot"},
...         ]},
...         {"name": "Bob", "pets": [
...             {"type": "budgie", "name": "Bertie"},
...         ]},
...     ]
... })

# We can get the names of the "pets" collection under the people "collection"
>>> roamer.people[:].pets.name()
('Mog', 'Spot', 'Bertie')

# And look up just the n-th result at at a given level
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
