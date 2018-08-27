<img src="http://mypy-lang.org/static/mypy_light.svg" alt="mypy logo" width="300px"/>

Mypy plugin and stubs for SQLAlchemy
====================================

[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)

This package contains [type stubs](https://www.python.org/dev/peps/pep-0561/) and a
mypy plugin to provide more precise static types
and type inference for [SQLAlchemy framework](http://docs.sqlalchemy.org/en/latest/).
SQLAlchemy uses some Python "magic" that
makes having precise types for some code patterns problematic. This is why we need to
accompany the stubs with mypy plugins. The final goal is to be able to get precise types
for most common patterns. A simple example:

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)

user = User(id=1, name='John', address='john@mail.org')  # Error, unexpected argument 'address'
user.id  # Inferred type "int"
User.id  # Inferred type is "Column[int]"
```

## Installation

To install the latest version of the package:
```
git clone ... && cd sqlalchemy-stubs && pip install -U .
```

After the 0.1 version will be released on PyPI, one can install latest
stable version as:
```
pip install -U sqlalchemy-stubs
```

## Development status

The package is currently in pre-alpha stage. See issue tracker for bugs and missing
features. If you want to contribute, a good place to start is `help-wanted` label (link).

The 0.1 version will be released when we will support ..., see issues ...

The long term goal is to be able to infer types for something as complex as ...
(two examples for old-style, and two for new-style).

External contributions to the project should be subject to
[Dropbox Contributor License Agreement (CLA)](https://opensource.dropbox.com/cla/).

--------------------------------
Copyright (c) 2018 Dropbox, Inc.

