Getting Started
---------------

To start debugging, simply insert::

    from pudb import set_trace; set_trace()

A shorter alternative to this is::

    import pudb; pu.db

Or, if pudb is already imported, just this will suffice::

    pu.db

Insert either of these snippets into the piece of code you want to debug, or
run the entire script with::

    pudb my-script.py

or, in Python 3::

    pudb3 my-script.py

This is equivalent to::

    python -m pudb.run my-script.py

which is useful if you want to run PuDB in a version of Python other than the
one you most recently installed PuDB with.

Debugging from a separate terminal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It's possible to control the debugger from a separate terminal. This is useful
if there are several threads running that are printing to stdout while
you're debugging and messing up the terminal, or if you want to keep the
original terminal available for any other reason.

To create a new terminal, use the utility script (tmux must be installed)::

    python -m pudb.create_tty

Then set the PUDB_TTY environment variable to this path, for example::

    PUDB_TTY=/dev/pts/3 pudb my-script.py

Now instead of using the current terminal, pudb will use this tty for its UI.

Remote debugging
^^^^^^^^^^^^^^^^

Rudimentary remote debugging is also supported::

    from pudb.remote import set_trace
    set_trace(term_size=(80, 24))

At this point, the debugger will look for a free port and wait for a telnet
connection::

    pudb:6899: Please telnet into 127.0.0.1 6899.
    pudb:6899: Waiting for client...

Usage with pytest
^^^^^^^^^^^^^^^^^

To use PuDB with `pytest <http://docs.pytest.org/en/latest/>`_, consider
using the `pytest-pudb <https://pypi.python.org/pypi/pytest-pudb>`_ plugin.

Alternatively, as of version 2017.1.2, pudb can be used to debug test failures
in `pytest <http://docs.pytest.org/en/latest/>`_, by running the test runner
like so::

    $ pytest --pdbcls pudb.debugger:Debugger --pdb --capture=no

Note the need to pass --capture=no (or its synonym -s) as otherwise
pytest tries to manage the standard streams itself. (contributed by Antony Lee)


