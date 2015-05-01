[![Build Status](https://travis-ci.org/touilleMan/samarche.svg)](https://travis-ci.org/touilleMan/samarche)

Samarche
========

API checker inspired by [this post](http://sametmax.com/est-ce-que-cet-outil-existe-en-python/)

Quickstart
----------

Say you're developping a module with a public API, for people working with it, this API is supposed to stay the same until the next major release. What would happen if a commit makes a change it shouldn't have ?

The solution is testing :
```python
# A class which is part of your API
class Foo:
    bar = True
    def __init__(self, stuff=False):
        self.stuff
 
    def thing(self):
        return "doh"
 
# Your tests to make sure the class stay consistent
self.assertTrue(hasattr(Foo, 'bar'))
self.assertTrue(hasattr(Foo, 'thing'))
self.assertTrue(hasattr(Foo(), 'stuff'))
```

Unfortunatly those tests are basically writting all your API a second time, there must be a better (and less boring) way ! 

Samarche allow you to take a snapshop of your API (called a `signature`) and then be able to test your evolving codebase against it.

Samarche register only public members (i.e. everything starting by `_` is skiped)
You can create signatures from a `module`, `module.package` and even `module.package:package_attribute`


Example
-------

First build and save the signature of your API:
```python
# Do this at each major release
import samarche

signature = samarche.build_signature("my_api")
with open('my_api.signature', 'wb') as fd:
  samarche.dump(signature, f)
```

Then put somewhere in your tests
```python
with open('my_api.signature', 'rb') as fd:
  original_signature = samarche.load(fd)
try:
  samarche.check_signature('my_api', original_signature)
except samarche.ValidationError as e:
  print("API has changed : {}".format(e))
```
