# roam – Easily traverse nested Python data structures

**roam** provides an API to more easily traverse nested data structures using standard Python syntax, without pesky error-handling at each step. 

For example, with data like that
```python
data = {
    "answer": {"to": {"the": {"ultimate": {"question": 42}}}},
    "panic": False,
    "species-by-intelligence": [
        {"name": "mice"},
        {"name": "dolphins", "message": "So long, and thanks for all the fish"},
        {"name": "humans"},
    ],
}
```

**roam** lets you do this
```python
import roam
r = roam.Roamer(data)

# Use dot notation to traverse `dict` keys
r.answer.to.the.ultimate.question()  # => 42

# Or slice notation, or both
r["answer"].to.the["ultimate"].question()  # => 42

# An invalid path returns a MISSING item placeholder, not an error 
answer = r.answer.to.the.WRONG.question()  # => <Roam.MISSING>

# You can check whether you got a valid result
answer is roam.MISSING  # True
if not answer:
    "Panic!"  # => 'Panic!'

# Or you can get a *helpful* exception, if you prefer  
r.answer.to.the.WRONG.question(_raise=True)
# => <RoamPathException: missing step 4 .WRONG for path 
#    <dict>.answer.to.the.WRONG.question at <dict> with keys ['ultimate']>

# Iterate over items (with slice notation if "dot" name would be invalid)
[(i, species.name()) for i, species in enumerate(r["species-by-intelligence"])]
# => [(0, 'mice'), (1, 'dolphins'), (2, 'humans')]

# Get just the path results available a collection
r["species-by-intelligence"][:].message()
# => ('So long, and thanks for all the fish',)
```

Which is easier than the contortions you might need without **roam**
```python
# Traverse `dict` keys defensively, hoping you don't hit a `None` value
data.get("answer", {}).get("to", {}).get("the", {}).get("ultimate", {}).get("question")  # => 42

# If you are not defensive, errors for invalid path aren't always helpful
data["answer"]["to"]["the"]["the"]["WRONG"]["question"]  # => KeyError: 'the'

# Get just the path results available a collection
[i["message"] for i in data["species-by-intelligence"] if "message" in i]
# => ['So long, and thanks for all the fish']
```


## Core concepts

- create a `Roamer` with your data
- express paths with dot or slice lookups
- "call" to get the result
- handling collections with slices
- missing results


## Installation

[Coming soon] Install **roam** with pip:

```
$ pip install roam
``` 

**roam** works with Python versions 3.4 and later.


## Understand the basics

- express paths using Python "dot" or "index" syntax, in any combination. **roam* will perform attribute or index lookups as needed
- "call" as a function to fetch the result 
- the `roam.MISSING` placeholder
- traversing collections
- rich path exceptions
- rich path description


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
- [glom](https://glom.readthedocs.io/) – Restructuring data, the Python way.
- [traversify](https://pypi.org/project/traversify/) – Handy python classes for manipulating json data, providing syntactic sugar for less verbose, easier to write code.


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
