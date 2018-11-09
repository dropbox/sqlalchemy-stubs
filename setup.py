from distutils.core import setup
import os

name = 'sqlalchemy-stubs'
description = 'Experimental SQLAlchemy stubs'

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
      version='0.1',
      description=description,
      long_description=description,
      author='Ivan Levkivskyi',
      author_email='levkivskyi@gmail.com',
      license='MIT License',
      py_modules=['sqlmypy'],
      install_requires=[
          'typing-extensions>=3.6.5'
      ],
      packages=['sqlalchemy-stubs'],
      package_data={'sqlalchemy-stubs': find_stub_files()},
)
