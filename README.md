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

<!-- TOC depthFrom:2 insertAnchor:true -->

- [Installation](#installation)
- [Basics](#basics)
    - [The `Roamer` shim](#the-roamer-shim)
    - [Express a path to traverse](#express-a-path-to-traverse)
    - [Get a result, or `MISSING`](#get-a-result-or-missing)
    - [Helpful path descriptions and exceptions](#helpful-path-descriptions-and-exceptions)
    - [Traverse collections](#traverse-collections)
- [Advanced](#advanced)
    - [Raise exceptions by default](#raise-exceptions-by-default)
    - [Work with `Roamer` shim objects directly](#work-with-roamer-shim-objects-directly)
    - [Get underlying data without using the `Roamer` *call* mechanism](#get-underlying-data-without-using-the-roamer-call-mechanism)
    - [Call methods on or in your data](#call-methods-on-or-in-your-data)
    - [A note on naming of parameters and internal variables](#a-note-on-naming-of-parameters-and-internal-variables)
- [Related projects](#related-projects)
- [Contributing](#contributing)
- [License](#license)

<!-- /TOC -->

<a id="markdown-installation" name="installation"></a>
## Installation

[Install **roam**](https://pypi.org/project/roam/) with pip:

```bash
$ pip install roam
``` 

**roam** works with Python versions 3.6 and later and has no dependencies.


<a id="markdown-basics" name="basics"></a>
## Basics

<a id="markdown-the-roamer-shim" name="the-roamer-shim"></a>
### The `Roamer` shim

**roam** works by providing the `Roamer` class to serve as a shim over your data objects, to intercept Python operations and do the extra work required to more easily traverse nested data.

Make a shim for your data by calling `roam.Roamer(data)` or you can use the shorter `r` alias function: `roam.r(data)`

<a id="markdown-express-a-path-to-traverse" name="express-a-path-to-traverse"></a>
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

<a id="markdown-get-a-result-or-missing" name="get-a-result-or-missing"></a>
### Get a result, or `MISSING`

You get a final result by *calling* the shim `Roamer` object like a function with `()` parentheses, which tells **roam** to return the underlying data.

If you expressed a valid path through your data, you will get the result you expect.

If you expressed an *invalid* path, **roam** will *not* complain or raise an exception. Instead, it will return a `roam.MISSING` marker object to let you know that there was no data available at the path.

You can check for the `roam.MISSING` marker object directly if you want, but this marker is "falsey" in a number of ways which also makes it easy to act on a missing result without explicitly checking for one:

```python
>>> roamer = roam.r(Point(x=100, y=200))

# Check for the <MISSING> object directly
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

<a id="markdown-helpful-path-descriptions-and-exceptions" name="helpful-path-descriptions-and-exceptions"></a>
### Helpful path descriptions and exceptions

To help you know where you are when traversing your data, or where your traversal path went wrong, **roam** keeps track of the path you have taken and presents it in the descriptive text of `Roamer` and `RoamPathException` objects.

```python
>>> roamer = roam.r({"a": {"b": ["value1", "value2"]}})

# The Roamer `repr` / `str` description tells you where you are...
>>> roamer.a.b[0]
<Roamer: <dict>.a.b[0] => 'value1'>

# ...and where you went wrong
>>> roamer.a.b[9]
<Roamer: missing step 3 [9] for path <dict>.a.b[9] at <list> with length 2 => <MISSING>>

# As does the RoamPathException you can optionally trigger
>>> roamer.a[9].all["kinds"].of.WRONG(_raise=True)
Traceback (most recent call last):
roam.RoamPathException: <RoamPathException: missing step 2 [9] for path <dict>.a[9].all['kinds'].of.WRONG at <dict> with keys ['b']>

```

<a id="markdown-traverse-collections" name="traverse-collections"></a>
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
<MISSING>

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

**WARNING**: **roam** has only rudimentary support for traversing nested collections: it always flattens the data. This should be fine for simple situations, but if you need to get nested results from collections you will need to use nested loops in Python code, or try the related project [glom](#related-projects) as an alternative.

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


<a id="markdown-advanced" name="advanced"></a>
## Advanced

<a id="markdown-raise-exceptions-by-default" name="raise-exceptions-by-default"></a>
### Raise exceptions by default

If you dislike getting `roam.MISSING` marker objects instead of an exception when you express an invalid path, you can make **roam** raise an exception immediately by setting a preference flag that will apply to all future generated shim objects.

Provide the `_raise` parameter when constructing a `Roamer` object or use the `roam.r_strict` helper function:

```python
>>> data = {"valid": {"stillValid": 123}}

# These two are equivalent
>>> roamer = roam.r(data, _raise=True)
>>> roamer = roam.r_strict(data)

# A strict/raising Roamer works as usual for valid paths...
>>> roamer.valid.stillValid
<Roamer: <dict>.valid.stillValid => 123>

# ...but will fail *immediately* on an invalid path, even if you don't call the shim. 
>>> try:
...     roamer.valid.stillValid.nope.sorry
... except roam.RoamPathException as ex:
...     str(ex)
'<RoamPathException: missing step 3 .nope for path <dict>.valid.stillValid.nope at <int>>'

# Notice this  exception path only goes as far as the first invalid step  ^^^^^
```


<a id="markdown-work-with-roamer-shim-objects-directly" name="work-with-roamer-shim-objects-directly"></a>
### Work with `Roamer` shim objects directly

Although the main goal of the `Roamer` shim object is to traverse paths through your data, it has additional features to let you work with your data without the need to *call* the shim.

A `Roamer` object lets you:

- perform equality comparisons on the underlying data, so you can check whether your data matches expected values while it is still within the shim:

  ```python
  >>> roamer = roam.r({"name": ["my", "test", "values"]})

  # Checking equality of returned data works as you expect
  >>> roamer.name() == ["my", "test", "values"]
  True

  # But you can also check equality without calling the shim
  >>> roamer.name == ["my", "test", "values"]
  True

  ```

- iterate over your data and get a `Roamer` shim for each item, so you can keep traversing deeper within collections:

  ```python
  >>> roamer = roam.r({"members": [
  ...     {"name": "John"}, {"name": "Paul"}, {"name": "George"}, {"name": "Ringo"},
  ... ]})

  # You can iterate over returned data as you expect
  >>> [member for member in roamer.members()]
  [{'name': 'John'}, {'name': 'Paul'}, {'name': 'George'}, {'name': 'Ringo'}]

  # But you can also iterate over the shim, and get a shim for each data item
  >>> [member.name() for member in roamer.members]
  ['John', 'Paul', 'George', 'Ringo']

  # Iterating over an invalid path will simply return no results
  >>> [member.name() for member in roamer.wrong.path]
  []

  ```

- get the length of your underlying data:

  ```python
  # len() on the shim returns the length of your underlying data
  >>> len(roamer.members)
  4

  # len() for an invalid path returns zero
  >>> len(roamer.wrong.path)
  0

  ```

- get the truthiness of your underlying data:

  ```python
  >>> if roamer.members:
  ...     "Truthy"
  'Truthy'

  >>> if not roamer.wrong.path:
  ...     "Falsey"
  'Falsey'

  ```

<a id="markdown-get-underlying-data-without-using-the-roamer-call-mechanism" name="get-underlying-data-without-using-the-roamer-call-mechanism"></a>
### Get underlying data without using the `Roamer` *call* mechanism

If you would prefer to get your underlying data from a `Roamer` without using the calling mechanism, or if the semi-magical behaviour is causing problems, you can get the data more directly with the `roam.unwrap` function.

```python
>>> roamer = roam.r({"a": {"b": {"c": "value"}}})

# The two approaches are equivalent for valid paths...
>>> roamer.a.b.c()
'value'
>>> roam.unwrap(roamer.a.b.c)
'value'

# ...and for invalid paths...
>>> roamer.a.b.c.x()
<MISSING>
>>> roam.unwrap(roamer.a.b.c.x)
<MISSING>

# ...and for invalid paths where you want an exception
>>> roamer.a.b.c.x(_raise=True)
Traceback (most recent call last):
roam.RoamPathException: <RoamPathException: missing step 4 .x for path <dict>.a.b.c.x at <str>>
>>> roam.unwrap(roamer.a.b.c.x, _raise=True)
Traceback (most recent call last):
roam.RoamPathException: <RoamPathException: missing step 4 .x for path <dict>.a.b.c.x at <str>>

```

<a id="markdown-call-methods-on-or-in-your-data" name="call-methods-on-or-in-your-data"></a>
### Call methods on or in your data

Calling a `Roamer` shim with `()` returns the underlying data, but this mechanism has more powerful features. It also lets call methods on or in your data with arguments you provide, or invoke arbitrary functions.

If your path ends at a *callable* object, **roam** will perform that call while returning your data:
```python
>>> roamer = roam.r({"callables": [
...     lambda: "I was called when returned",
...     lambda a, b: f"I was called with {a} and {b} which sum to {a + b}",
... ]})

# A basic () call on a shim invokes the callable object before returning
>>> roamer.callables[0]()
'I was called when returned'

# Arguments are passed through to the callable when returning
>>> roamer.callables[1](3, 5)
'I was called with 3 and 5 which sum to 8'

```

You can pass a function in to **roam** with the `_invoke` parameter when returning data to invoke that function with your underlying data as the first argument:
```python
>>> roamer = roam.r({"unsorted": [4, 6, 2, 9]})

# We can get our data directly, but it would be nice if it was sorted
>>> roamer.unsorted()
[4, 6, 2, 9]

# Get roam to do the sorting for us using Python's built-in function
>>> roamer.unsorted(_invoke=sorted)
[2, 4, 6, 9]

```

If you need to invoke a callable in your data and then continue traversing its results, you can tell **roam** to re-wrap the result of a call in another shim with the `_roam` parameter:
```python
>>> roamer = roam.r({"callables": [
...    lambda: {"more": {"nested": "data"}},
...    lambda: {"more": {"nested": "data"}},
... ]})

# The callable returns nested data
>>> roamer.callables[0]()
{'more': {'nested': 'data'}}

# Re-wrap the result of the callable in a new shim
>>> shim_result = roamer.callables[0](_roam=True)
>>> shim_result
<Roamer: <dict>.callables[0] => {'more': {'nested': 'data'}}>

>>> shim_result.more.nested()
'data'

```

<a id="markdown-a-note-on-naming-of-parameters-and-internal-variables" name="a-note-on-naming-of-parameters-and-internal-variables"></a>
### A note on naming of parameters and internal variables

Because **roam** uses some voodoo to intercept and reinterpret path operations expressed in standard Python syntax, the library must avoid naming parameters or internal variables in a way that will clash with names in your real data.

For this reason the parameters you can pass when creating a `Roamer` object or calling it to return data are awkwardly named. Hopefully the parameters `_invoke`, `_roam`, and `_raise` will not match parameters you want to pass through the shim to callables in your data.

Similarly the internal variable names within `Roamer` have nasty names like `_r_item_` and `_r_path_` which should be *very* unlikely to clash with key or attribute names in real-world data. If you do have names like this in your data, stop it!


<a id="markdown-related-projects" name="related-projects"></a>
## Related projects

These similar tools and libraries inspired and informed **roam**:

- [glom](https://glom.readthedocs.io/) – *Restructuring data, the Python way.*  
  This library's data access and [glom.T](https://glom.readthedocs.io/en/latest/api.html#glom.T) components do everything **roam** does and more, while **roam** aims to be smaller and simpler. If you find **roam** too limiting, **glom** is the library you want.
- The Django template language's [variable dot lookup](https://docs.djangoproject.com/en/2.2/ref/templates/language/#variables) gave us a taste for dot-path data traversal in the first place.
- [jmespath](https://pypi.org/project/jmespath/) – *JMESPath (pronounced “james path”) allows you to declaratively specify how to extract elements from a JSON document.*
- [traversify](https://pypi.org/project/traversify/) – *Handy python classes for manipulating json data, providing syntactic sugar for less verbose, easier to write code.*


<a id="markdown-contributing" name="contributing"></a>
## Contributing

We would love to get your help to improve **roam**!

Please contribute by trying the project for yourself, report bugs you find of feature requests as [issues in GitHub](https://github.com/jmurty/roam/issues), and if you like get your hands dirty in the code.

Please note that all contributors must follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Be kind, be awesome!

To get started working on the **roam** codebase:

1. Clone the repository directly from GitHub: `git clone git@github.com:jmurty/roam.git`
   - Alternatively [fork the repository](https://guides.github.com/activities/forking/) to work on your own version.
1. [Install Python](https://www.python.org/downloads/) **version 3.6** or greater
   - Consider using [pyenv](https://github.com/pyenv/pyenv) to install and manage the latest Python versions.
1. [Install Pipenv](https://pipenv.readthedocs.io/en/latest/#install-pipenv-today)
1. Change to the *roam/* repository directory
1. Create a development virtualenv: `pipenv install --dev`
1. **Explore and improve the code**
1. Run all code unit tests: `pytest`
   - Run code and documentation tests with a coverage report: `pytest -c pytest-with-cov-docs.ini`
1. The **roam** project requires that Python code be formatted with [Black](https://github.com/python/black) for consistency. Before sharing code changes: `black .`
   - Install a Git pre-commit hook with the [pre-commit](https://pre-commit.com) tool to run `black` automatically before you commit changes: `pre-commit install-hooks`
1. Use [Tox](https://tox.readthedocs.io/en/latest/) to run all unit, documentation, and formatting tests across multiple Python versions 3with `tox`
   - You must have installed the Python versions configured in the *tox.ini* for this to work.
1. Please submit code changes as [GitHub pull requests](https://guides.github.com/activities/forking/#making-a-pull-request). 


<a id="markdown-license" name="license"></a>
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
