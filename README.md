# roam – Easily traverse nested Python data structures

**roam** provides an API to more easily traverse nested data structures using standard Python syntax without pesky error-handling at each step. 

[![Build Status](https://travis-ci.org/jmurty/roam.svg?branch=master)](https://travis-ci.org/jmurty/roam)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

Here is a quick introduction to **roam**ing nested data:
```python
# Example data
>>> data = {
...     "answer": {"to": {"the": {"ultimate": {"question": 42}}}},
...     "speciesByIntelligence": [
...         {"name": "mice"},
...         {"name": "dolphins", "message": "So long, and thanks for all the fish"},
...         {"name": "humans"},
...     ],
... }

# Wrap your data in a Roamer class
>>> import roam
>>> roamer = roam.Roamer(data)

# Use dot notation to traverse `dict` keys
>>> roamer.answer.to.the.ultimate.question()
42

# Slice notation still works, or you can mix and match
>>> roamer["answer"].to.the["ultimate"].question() 
42

# Invalid paths don't raise an error, they return a MISSING marker object 
>>> result = roamer.answer.to.the.WRONG.question()
>>> result
<Roam.MISSING>

# The MISSING marker object is falsey in many dimensions
>>> bool(result)
False
>>> len(result)
0
>>> [x for x in result]
[]

# This makes it easy to get data at a path or fall back to a default
>>> roamer.non.existent.path() or "My fallback"
'My fallback'
>>> roamer.answer.to.the.ultimate() or "penultimate"
{'question': 42}

# If you would prefer an exception you can ask `roam` to raise one:  
>>> try:
...     roamer.answer.to.the.the.ultimate.question(_raise=True)
... except roam.RoamPathException as ex:
...     str(ex)
"<RoamPathException: missing step 4 .the for path <dict>.answer.to.the.the.ultimate.question at <dict> with keys ['ultimate']>"

# And you can traverse collections in your data. Tell `roam` to handle collections with a slice
# operator and its behaviour changes to *filter* results from valid paths, even deep paths
>>> len(roamer["speciesByIntelligence"])
3
>>> roamer["speciesByIntelligence"][:].name()
('mice', 'dolphins', 'humans')
>>> roamer["speciesByIntelligence"][:].message()
('So long, and thanks for all the fish',)

```

Compare that with the kind of code you might need without **roam**
```python
# A  dotted path would be nicer here
>>> data["answer"]["to"]["the"]["ultimate"]["question"]
42

# Traversing `dict` keys defensively is ugly but works, unless you hit a `None` value part way
>>> data.get("answer", {}).get("to", {}).get("the", {}).get("ultimate", {}).get("question") or "Oops"
42
>>> data.get("answer", {}).get("to", {}).get("the", {}).get("WRONG", {}).get("question") or "Oops"
'Oops'

# Standard errors for invalid paths aren't as clear
>>> data["answer"]["to"]["the"]["the"]["ultimate"]["question"]
Traceback (innermost last):
KeyError: 'the'

# Filtering collections in your data is cumbersome
>>> [i["message"] for i in data["speciesByIntelligence"] if "message" in i]
['So long, and thanks for all the fish']

```


## Installation

Install **roam** with pip:

```
$ pip install roam
``` 

**roam** works with Python versions 3.6 and later.


## Basics

**roam** works as a shim over data objects that intercepts Python operations and does extra work to make data traversal easier and more forgiving.

There are three key steps you need to use **roam**:

1. make a `Roamer` shim for your data with `roam.Roamer(data)` or with the more concise `r` alias `roam.r(data)`:  
   `shim = roam.r(data)`
2. express the path or paths to traverse through your data in Python attribute (dot) or key/index (slice) syntax
   - you can use dot syntax whether the underlying objects support attribute or index lookups:   
     `step = shim.path.to.traverse`
   - you can also use key/index lookups if you prefer, or if you need to traverse a path that is not a valid Python attribute name:  
     `step = shim.path.to["step through"]`
   - if your data includes collections of items like lists, expressing a slice operation instructs **roam** to apply following path lookups to **each item** in the collection, and to ignore items in the collection that don't match the following path.  
     Think of a slice in **roam** paths as being like a combined *for-each* and *filter*.  
     You can process all items in the collection with the special `[:]` slice, or a subset using `[2:3]` etc:  
     `step = shim.path.to.list[:].path.in.each.list.item`
   - an integer index lookup will get the *i-th* item in a collection as you would expect:  
     `step = shim.path.to.list[:].nested.list[0]  # first item in each nested list`
3. retrieve a final result by *calling* the shim object, which tells **roam** to return the underlying data
   - if the path you expressed was valid, you will get your result data:  
     `result = step()`
   - if the path included a slice operation to process items in a collection, the result will be a tuple of matching items:  
     `multiple_results = step()` 
   - if you expressed an invalid path, you will instead get the `roam.MISSING` marker object. You can check for this result directly, or rely on its falsey-ness:  
     `assert step() is roam.MISSING`
     `assert not step()`


## Advanced topics

- falsey-ness of `roam.MISSING`
- rich path descriptions and exceptions
- **roam** is a shim (lookup order, equality, iteration, falsey-ness, truthiness, length)
- call nested methods
- re-wrap result of nested method call with the `_roam` option
- fail fast with the `_raise` option
- call arbitrary functions with the `_invoke` option


## Related projects

These similar tools and libraries helped inspire and inform *roam*:

- Django template language's [variable dot lookup](https://docs.djangoproject.com/en/2.2/ref/templates/language/#variables)
- [glom](https://glom.readthedocs.io/) – "Restructuring data, the Python way."
- [traversify](https://pypi.org/project/traversify/) – "Handy python classes for manipulating json data, providing syntactic sugar for less verbose, easier to write code."


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
