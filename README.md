# roam – Easily traverse nested Python data structures

**roam** provides an API to more easily traverse nested data structures using standard Python syntax without pesky error-handling at each step. 

[![Build Status](https://travis-ci.org/jmurty/roam.svg?branch=master)](https://travis-ci.org/jmurty/roam)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

Here are some examples of **roam**ing nested data:
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
>>> answer = roamer.answer.to.the.WRONG.question()
>>> answer
<Roam.MISSING>

# The MISSING marker object is falsey in many dimensions
>>> bool(answer)
False
>>> len(answer)
0
>>> [x for x in answer]
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


## Core concepts

- create a `Roamer` with your data
- express paths using Python "dot" or "index" syntax, in any combination. **roam* will perform attribute or index lookups as needed
- "call" as a function to fetch the result 
- the `roam.MISSING` placeholder
- traverse collections with slices
- rich path descriptions and exceptions


## Advanced topics

- **roam** is a shim (lookup order, equality, iteration, falsey-ness, truthiness)
- `roam.MISSING` is falsey
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

- TODO: [Code of conduct](https://opensource.guide/code-of-conduct/)
- We use the Black code formatter
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
