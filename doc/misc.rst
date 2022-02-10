Installing
----------

Install PuDB using the command::

    pip install pudb

If you are using Python 2.5, PuDB version 2013.5.1 is the last version to
support that version of Python. urwid 1.1.1 works with Python 2.5, newer
versions do not.

.. _faq:

FAQ
---

**Q: I navigated to the Variables/Stack/Breakpoints view.  How do I get
back to the source view?**

A: Press your left arrow key.

**Q: Where are breakpoints, PuDB settings file or shell history stored?**

A: All PuDB information is stored in a location specified by the `XDG Base
Directory Specification
<http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_.
Usually, it is ``~/.config/pudb``.  Breakpoints are stored in a file called
``saved-breakpoints``.  Also in this location are the shell history from the
``!`` shell (``shell-history``) and the PuDB settings (``pudb.cfg``).

**Q: I killed PuDB and now my terminal is broken.  How do I fix it?**

A: Type the ``reset`` command (even if you cannot see what you are typing, it
should work).  If this happens on a regular basis, please report it as a bug.

License and Dependencies
------------------------

PuDB is distributed under the MIT license. It relies on the following
excellent pieces of software:

* Ian Ward's `urwid <http://excess.org/urwid>`_ console UI library
* Georg Brandl's `pygments <http://pygments.org>`_ syntax highlighter

.. include:: ../LICENSE

