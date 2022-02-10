Starting the debugger without breaking
--------------------------------------

To start the debugger without actually pausing use::

    from pudb import set_trace; set_trace(paused=False)

at the top of your code.  This will start the debugger without breaking, and
run it until a predefined breakpoint is hit. You can also press ``b`` on a
``set_trace`` call inside the debugger, and it will prevent it from stopping
there.

Interrupt Handlers
------------------

``set_trace`` sets ``SIGINT`` (i.e., ``Ctrl-c``) to run ``set_trace``, so that
typing ``Ctrl-c`` while your code is running will break the code and start
debugging. See the docstring of ``set_interrupt_handler`` for more
information. Note that this only works in the main thread.

Programming PuDB
----------------

At the programming language level, PuDB displays the same interface
as Python's built-in `pdb module <http://docs.python.org/library/pdb.html>`_.
Just replace ``pdb`` with ``pudb``.
(One exception: ``run`` is called ``runstatement``.)

Controlling How Values Get Shown
--------------------------------

*   Set a custom stringifer in the preferences.

    An example file might look like this::

        def pudb_stringifier(obj):
            return "HI"

*   Add a method ``safely_stringify_for_pudb`` to the type.

A stringifier is expected to *never* raise an exception.
If an exception is raised, pudb will silently fall back
to its built-in stringification behavior.

A stringifier that takes a long time will further stall
the debugger UI while it runs.

Configuring PuDB
----------------

Overriding default key bindings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Configure in the settings file (see :ref:`faq`).

- Add the bindings under mentioned section in the config file
  (see :ref:`urwid:keyboard-input`).

- Only few actions are supported currently, coverage will increase with time.
  (Contributions welcome!)

.. code-block:: ini

    [pudb]

    # window chooser bindings
    hotkeys_breakpoints = B
    hotkeys_code = C
    hotkeys_stack = S
    hotkeys_variables = V
