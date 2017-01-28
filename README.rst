Pycycle: Find and fix circular imports in python projects
=========================================================

.. image:: https://img.shields.io/pypi/v/pycycle.svg
    :target: https://pypi.python.org/pypi/pycycle

.. image:: https://img.shields.io/pypi/l/pycycle.svg
    :target: https://pypi.python.org/pypi/pycycle

.. image:: https://img.shields.io/pypi/wheel/pycycle.svg
    :target: https://pypi.python.org/pypi/pycycle

.. image:: https://img.shields.io/pypi/pyversions/pipenv.svg
    :target: https://pypi.python.org/pypi/pycycle

.. image:: https://travis-ci.org/bndr/pycycle.svg?branch=master
    :target: https://travis-ci.org/bndr/pycycle

---------------


**Pycycle** is an experimental project that aims to help developers fix their circular dependencies problems.
`ImportError: Cannot import name X` is a python exception that is related to the circular imports, but it's not clear from the start.
This tool automatically analyzes the imports of your projects, and looks for imports that may cause a circular dependency problem.

Features
--------

- **Shows you the whole chain of the circular imports.**
- Gives you lines of code where each import is, for you to easily find and fix the problem.
- Visualizes your imports in a graph **(Not Yet Implemented)**



Usage
-----

::

    $ pycycle
    Usage: pycycle [OPTIONS] COMMAND [ARGS]...


    Examples:
        Get the circular imports in current project:
        $ pycycle --here
        Look for circular imports in another project
        $ pycycle --source /home/user/workspace/awesome_project

    Options:
      --verbose      Verbose output.
      --here         Try to find cycles in the current project
      --source TEXT  Try to find cycles in the path provided
      --help         Show this message then exit.
      --version      Show the version and exit.

::

    $ pycycle --here
    Project successfully transformed to AST, checking imports for cycles..
    Cycle Found :(
    a_module.a_file: Line 1 -> a_module.b_module.b_file: Line 1 -> c_module.c_file: Line 1 -> d_module.d_file: Line 1 =>> a_module.a_file
    Finished.

::

    $ pycycle --source /Users/vkravcenko/workspace/awesome_project
    Target source provided:/Users/vkravcenko/workspace/awesome_project
    Project successfully transformed to AST, checking imports for cycles..
    No worries, no cycles here!
    If you think some cycle was missed, please open an Issue on Github.
    Finished.


Installation
------------

::

    $ pip install pycycle