# roam – Easily traverse nested Python data structures

**roam** provides an API to more easily traverse nested data structures using standard Python syntax, without pesky error-handling at each step. 

**roam** lets you do this with nested data:
```python
# Example data
>>> data = {
...   "answer": {"to": {"the": {"ultimate": {"question": 42}}}},
...   "speciesByIntelligence": [
...     {"name": "mice"},
...     {"name": "dolphins", "message": "So long, and thanks for all the fish"},
...     {"name": "humans"},
...   ],
... }


# Wrap your data in a Roamer class
>>> import roam
>>> r = roam.Roamer(data)

# Use dot notation to traverse `dict` keys
>>> r.answer.to.the.ultimate.question()
42

# Or slice notation, or mix and match
>>> r["answer"].to.the["ultimate"].question() 
42

# An invalid path returns a MISSING item placeholder, not an error 
>>> answer = r.answer.to.the.WRONG.question()
>>> answer
<Roam.MISSING>

# You can check whether you got a valid result
>>> answer is roam.MISSING
True
>>> if not answer:
...  "Panic!"
'Panic!'

# Or you can get a *helpful* exception, if you prefer  
>>> try:
...   r.answer.to.the.WRONG.question(_raise=True)
... except roam.RoamPathException as ex:
...   str(ex)
"<RoamPathException: missing step 4 .WRONG for path <dict>.answer.to.the.WRONG.question at <dict> with keys ['ultimate']>"

# Iterate over items
>>> [(i, species.name()) for i, species in enumerate(r.speciesByIntelligence)]
[(0, 'mice'), (1, 'dolphins'), (2, 'humans')]

# Slice a collection to return only matching paths
>>> r["speciesByIntelligence"][:].message()
('So long, and thanks for all the fish',)

```

Compare that with the code contortions you might need without **roam**
```python
# Traverse `dict` keys defensively, hoping you don't hit a `None` value
>>> data.get("answer", {}).get("to", {}).get("the", {}).get("ultimate", {}).get("question")
42

# If you are not defensive, errors for invalid path aren't always helpful
>>> data["answer"]["to"]["the"]["the"]["ultimate"]["question"]
Traceback (innermost last):
KeyError: 'the'

# Get just the path results available a collection
>>> [i["message"] for i in data["speciesByIntelligence"] if "message" in i]
['So long, and thanks for all the fish']

```


## Installation

Install **roam** with pip:

```
$ pip install roam
``` 

**roam** works with Python versions 3.4 and later.


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
