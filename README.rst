PuDB is a full-screen, console-based visual debugger for Python.

Its goal is to provide all the niceties of modern GUI-based debuggers in a
more lightweight and keyboard-friendly package. PuDB allows you to debug code
right where you write and test it--in a terminal. If you've worked with the
excellent (but nowadays ancient) DOS-based Turbo Pascal or C tools, PuDB's UI
might look familiar.

Here's a screenshot:

.. image:: http://tiker.net/pub/pudb-screenshot.png

You may watch a `screencast <http://vimeo.com/5255125>`_, too.

Features
--------

* Syntax-highlighted source, the stack, breakpoints and variables are all
  visible at once and continuously updated. This helps you be more aware of
  what's going on in your program. Variable displays can be expanded, collapsed
  and have various customization options.

* Simple, keyboard-based navigation using single keystrokes makes debugging
  quick and easy. PuDB understands cursor-keys and Vi shortcuts for navigation.
  Other keys are inspired by the corresponding pdb coomands.

* Use search to find relevant source code, or use "m" to invoke the module
  browser that shows loaded modules, lets you load new ones and reload existing
  ones.

* Breakpoints can be set just by pointing at a source line and hitting "b" and
  then edited visually in the breakpoints window.  Or hit "t" to run to the line
  under the cursor.

* Drop to a Python shell in the current environment by pressing "!".

* PuDB places special emphasis on exception handling. A post-mortem mode makes
  it easy to retrace a crashing program's last steps.

* IPython integration (see `wiki <http://wiki.tiker.net/PuDB>`_)

* Should work with Python 2.4 and newer, including Python 3.

Installing
----------

Install PuDB using the command::

    easy_install pudb

Getting Started
---------------

To start debugging, simply insert::

    from pudb import set_trace; set_trace()

into the piece of code you want to debug, or run the entire script with::

    pudb my-script.py

or, in Python 3::

    pudb3 my-script.py

This is equivalent to::

    python -m pudb.run my-script.py

which is useful if you want to run PuDB in a version of Python other than the
one you most recently installed PuDB with.

Documentation and Support
-------------------------

PuDB has a `wiki <http://wiki.tiker.net/PuDB>`_, where documentation and
debugging wisdom are collected.

PuDB also has a `mailing list <http://lists.tiker.net/listinfo/pudb>`_ that
you may use to submit patches and requests for help.  You can also send a pull
request to the `GitHub repository <https://github.com/inducer/pudb>`_

Attaching to Running Code
-------------------------

An alternative to using ``set_trace`` is to use::

    from pudb import set_interrupt_handler; set_interrupt_handler()

at the top of your code.  This will set ``SIGINT`` (i.e., ``Ctrl-c``) to
run ``set_trace``, so that typing ``Ctrl-c`` while your code is running
will break the code and start debugging.  See the docstring of
``set_interrupt_handler`` for more information.

Programming PuDB
----------------

At the programming language level, PuDB displays the same interface
as Python's built-in `pdb module <http://docs.python.org/library/pdb.html>`_.
Just replace ``pdb`` with ``pudb``.
(One exception: ``run`` is called ``runstatement``.)

License and Dependencies
------------------------

PuDB is distributed under the MIT license. It relies on the following
excellent pieces of software:

* Ian Ward's `urwid <http://excess.org/urwid>`_ console UI library
* Georg Brandl's `pygments <http://pygments.org>`_ syntax highlighter

Development Version
-------------------

You may obtain the development version using the `Git <http://git-scm.org/>`_
version control tool.::

    git clone http://git.tiker.net/trees/pudb.git

You may also `browse the code <http://git.tiker.net/pudb.git>`_ online.

The repository is also mirrored at `GitHub <https://github.com/inducer/pudb>`_.

FAQ
---

**Q: I navigated to the Variables/Stack/Breakpoints view.  How do I get
back to the source view?**

A: Press your left arrow key.
