Starting the debugger
---------------------

To start debugging, simply insert::

    from pudb import set_trace; set_trace()

A shorter alternative to this is::

    import pudb; pu.db

Or, if pudb is already imported, just this will suffice::

    pu.db

If you are using Python 3.7 or newer, you can add::

    # Set breakpoint() in Python to call pudb
    export PYTHONBREAKPOINT="pudb.set_trace"

in your ``~/.bashrc``. Then use::

    breakpoint()

to start pudb.

Insert one of these snippets into the piece of code you want to debug, or
run the entire script with::

    python -m pudb my-script.py

which is useful if you want to run PuDB in a version of Python other than the
one you most recently installed PuDB with.

Debugging from a separate terminal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It's possible to control the debugger from a separate terminal. This is useful
if there are several threads running that are printing to stdout while
you're debugging and messing up the terminal, or if you want to keep the
original terminal available for any other reason.

Open a new terminal. First, you need to get the path of the tty of the
terminal you want to debug from. To do that, use the standard unix
command ``tty``. It will print something like ``/dev/pts/3``.

Then you need to make sure that your terminal doesn't have a shell actively
reading and possibly capturing some of the input that should go to pudb.
To do that run a placeholder command that does nothing,
such as ``perl -MPOSIX -e pause``.

Then set the PUDB_TTY environment variable to the path tty gave you,
for example::

    PUDB_TTY=/dev/pts/3 pudb my-script.py

Now instead of using the current terminal, pudb will use this tty for its UI.
You may want to use the internal shell in pudb, as others will still use the
original terminal.

Logging Internal Errors
^^^^^^^^^^^^^^^^^^^^^^^

Some kinds of internal exceptions encountered by pudb will be logged to the
terminal window when the debugger is active. To send these messages to a file
instead, use the ``--log-errors`` flag::

    python -m pudb --log-errors pudberrors.log

Remote debugging
^^^^^^^^^^^^^^^^

Rudimentary remote debugging is also supported. To break into the debugger,
enabling you to connect via ``telnet``, use the following code::

    from pudb.remote import set_trace
    set_trace(term_size=(80, 24))

At this point, the debugger will look for a free port and wait for a telnet
connection::

    pudb:6899: Please start a telnet session using a command like:
    telnet 127.0.0.1 6899
    pudb:6899: Waiting for client...

To debug a function in a remote debugger (and examine any exceptions that
may occur), use code like the following:

.. literalinclude:: ../examples/remote-debug.py

Upon running this, again, the debugger will wait for a telnet connection.

The following programming interface is available for the remote debugger:

.. automodule:: pudb.remote

"Reverse" remote debugging
^^^^^^^^^^^^^^^^^^^^^^^^^^

In "reverse" remote debugging, pudb connects to a socket, rather than listening to one.

First open the socket and listen using the netcat(``nc``), as below.
Netcat of couse is not a telnet client, so it can behave diffrently than a telnet client.
By using the ```stty``` with "no echo: and "no buffering" input options, we
can make a socket that nonetheless behave simillarly::

    stty -echo -icanon && nc -l -p 6899

When using the BSD version netcat that ships with MacOS, a server can be started like this::

    stty -echo -icanon && nc -l 6899

Specify host and port in set_trace and set the *reverse* parameter to *True*::

    from pudb.remote import set_trace
    set_trace(reverse=True)

Then watch the debugger connect to netcat::

    pudb:9999: Now in session with 127.0.0.1:6899.

Using the debugger after forking
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In a forked process, no TTY is usually attached to stdin/stdout, which leads to errors
when debugging with standard pudb. E.g. consider this ``script.py``::

    from multiprocessing import Process
    def f(name):
        # breakpoint was introduced in Python 3.7
        breakpoint()
        print('hello', name)

    p = Process(target=f, args=('bob',))
    p.start()
    p.join()

Running it with standard pudb breaks::

    PYTHONBREAKPOINT=pudb.set_trace python script.py

However, on Unix systems, e.g. Linux & MacOS, debugging a forked
process is supported using ``pudb.forked.set_trace``::

    PYTHONBREAKPOINT=pudb.forked.set_trace python script.py


Usage with pytest
^^^^^^^^^^^^^^^^^

To use PuDB with `pytest <http://docs.pytest.org/en/latest/>`_, consider
using the `pytest-pudb <https://pypi.python.org/pypi/pytest-pudb>`_ plugin,
which provides a ``--pudb`` option that simplifies the procedure below.

Alternatively, as of version 2017.1.2, pudb can be used to debug test failures
in `pytest <http://docs.pytest.org/en/latest/>`_, by running the test runner
like so::

    $ pytest --pdbcls pudb.debugger:Debugger --pdb --capture=no

Note the need to pass --capture=no (or its synonym -s) as otherwise
pytest tries to manage the standard streams itself. (contributed by Antony Lee)
