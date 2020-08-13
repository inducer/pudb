PuDB: a console-based visual debugger for Python
================================================

.. image:: https://gitlab.tiker.net/inducer/pudb/badges/master/pipeline.svg
    :alt: Gitlab Build Status
    :target: https://gitlab.tiker.net/inducer/pudb/commits/master
.. image:: https://github.com/inducer/pudb/workflows/CI/badge.svg?branch=master&event=push
    :alt: Github Build Status
    :target: https://github.com/inducer/pudb/actions?query=branch%3Amaster+workflow%3ACI+event%3Apush
.. image:: https://badge.fury.io/py/pudb.png
    :alt: Python Package Index Release Page
    :target: https://pypi.org/project/pudb/

Its goal is to provide all the niceties of modern GUI-based debuggers in a
more lightweight and keyboard-friendly package. PuDB allows you to debug code
right where you write and test it--in a terminal. If you've worked with the
excellent (but nowadays ancient) DOS-based Turbo Pascal or C tools, PuDB's UI
might look familiar.

Here's a screenshot:

.. image:: https://tiker.net/pub/pudb-screenshot.png

You may watch a `screencast <http://vimeo.com/5255125>`_, too.

Features
--------

* Syntax-highlighted source, the stack, breakpoints and variables are all
  visible at once and continuously updated. This helps you be more aware of
  what's going on in your program. Variable displays can be expanded, collapsed
  and have various customization options.

* Simple, keyboard-based navigation using single keystrokes makes debugging
  quick and easy. PuDB understands cursor-keys and Vi shortcuts for navigation.
  Other keys are inspired by the corresponding pdb commands.

* Use search to find relevant source code, or use "m" to invoke the module
  browser that shows loaded modules, lets you load new ones and reload existing
  ones.

* Breakpoints can be set just by pointing at a source line and hitting "b" and
  then edited visually in the breakpoints window.  Or hit "t" to run to the line
  under the cursor.

* Drop to a Python shell in the current environment by pressing "!".
  Or open a command prompt alongside the source-code via "Ctrl-X".

* PuDB places special emphasis on exception handling. A post-mortem mode makes
  it easy to retrace a crashing program's last steps.

* Ability to control the debugger from a separate terminal.

* IPython integration (see `wiki <http://wiki.tiker.net/PuDB>`_)

* Should work with Python 3.6 and newer. (Versions 2019.2 and older continue
  to support Python 2.7.)

Links
-----

`PuDB documentation <https://documen.tician.de/pudb>`_

PuDB also has a `mailing list <http://lists.tiker.net/listinfo/pudb>`_ that
you may use to submit patches and requests for help.  You can also send a pull
request to the `GitHub repository <https://github.com/inducer/pudb>`_

Development Version
-------------------

You may obtain the development version using the `Git <http://git-scm.org/>`_
version control tool.::

    git clone https://github.com/inducer/pudb.git

You may also `browse the code <https://github.com/inducer/pudb>`_ online.
