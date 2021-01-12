from setuptools import setup
import os

name = 'sqlalchemy-stubs'
description = 'SQLAlchemy stubs and mypy plugin'

install_instructions = """\
# Experimental SQLAlchemy type stubs and mypy plugin

This package contains type stubs and mypy plugin to provide more precise
static types and type inference for SQLAlchemy framework. SQLAlchemy uses
dynamic Python features that are hard to understand by static type checkers,
this is why the plugin is needed in addition to type stubs.

Currently, some basic use cases like inferring model field types are supported.
The final goal is to be able to get precise types for most common patterns.

## Installation

```
pip install sqlalchemy-stubs
```

Important: you need to enable the plugin in your mypy config file:
```
[mypy]
plugins = sqlmypy
```
"""


def find_stub_files():
    result = []
    for root, dirs, files in os.walk(name):
        for file in files:
            if file.endswith('.pyi'):
                if os.path.sep in root:
                    sub_root = root.split(os.path.sep, 1)[-1]
                    file = os.path.join(sub_root, file)
                result.append(file)
    return result


setup(name='sqlalchemy-stubs',
      version='0.4',
      description=description,
      long_description=install_instructions,
      long_description_content_type='text/markdown',
      author='Ivan Levkivskyi',
      author_email='levkivskyi@gmail.com',
      license='MIT License',
      url="https://github.com/dropbox/sqlalchemy-stubs",
      py_modules=['sqlmypy', 'sqltyping'],
      install_requires=[
          'mypy>=0.790',
          'typing-extensions>=3.7.4'
      ],
      packages=['sqlalchemy-stubs'],
      package_data={'sqlalchemy-stubs': find_stub_files()},
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Programming Language :: Python :: 3'
      ]
)
