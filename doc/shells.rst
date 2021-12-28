Shells
======

Internal shell
--------------

At any point while debugging, press ``Ctrl-x`` to switch to the built in
interactive shell. From here, you can execute Python commands at the current
point of the debugger. Press ``Ctrl-x`` again to move back to the debugger.

Keyboard shortcuts defined in the internal shell:

+--------------------+--------------------+
|Enter               |Execute the current |
|                    |command             |
+--------------------+--------------------+
|Ctrl-v              |Insert a newline    |
|                    |(for multiline      |
|                    |commands)           |
+--------------------+--------------------+
|Ctrl-n/p            |Browse command      |
|                    |history             |
+--------------------+--------------------+
|Up/down arrow       |Select history      |
+--------------------+--------------------+
|TAB                 |Tab completion      |
+--------------------+--------------------+
|+/-                 |grow/shrink the     |
|                    |shell (when a       |
|                    |history item is     |
|                    |selected)           |
+--------------------+--------------------+
|_/=                 |minimize/maximize   |
|                    |the shell (when a   |
|                    |history item is     |
|                    |selected)           |
+--------------------+--------------------+

External shells
---------------

To open the external shell, press the ``!`` key while debugging. Unlike the
internal shell, external shells close the debugger UI while the shell is
active. Press ``Ctrl-d`` at any time to exit the shell and return to the
debugger.

To configure the shell used by PuDB, open the settings (``Ctrl-p``) and select
the shell.

PuDB supports the following external shells.

- Internal (same as pressing ``Ctrl-x``). This is the default.
- Classic (similar to the default ``python`` interactive shell)
- `IPython <https://ipython.org/>`_
   The `IPython` shell can also be used in a server-client fasion, which is
   enabled by selecting the shell `ipython_kernel` in the settings. When set,
   the ``!`` key will start an `IPython` kernel and wait for connection from,
   e.g., `qtconsole`. Like other shells, `ipython_kernel` blocks the debugger
   UI while it is active. Type `quit` or `exit` from a client to exit the
   kernel and return to the debugger.
- `bpython <https://bpython-interpreter.org/>`_
- `ptpython <https://github.com/jonathanslenders/ptpython>`_


Custom shells
-------------

To define a custom external shell, create a file with a function
``pudb_shell(_globals, _locals)`` at the module level. Then, in
the settings (``Ctrl-p``), select "Custom" under the shell settings, and add
the path to the file.

Here is an example custom shell file:

.. literalinclude:: ../examples/shell.py
   :language: python

Note, many shells do not allow passing in globals and locals dictionaries
separately. In this case, you can merge the two with

.. code-block:: python

   from pudb.shell import SetPropagatingDict
   ns = SetPropagatingDict([_locals, _globals], _locals)

Here is more information on ``SetPropagatingDict``:

.. autoclass:: pudb.shell.SetPropagatingDict
