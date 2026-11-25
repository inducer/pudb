Configuration
-------------

At debugging session ``Ctrl-P`` shortcut opens configuration dialog.
Additionally all PuDB information is stored in a location specified by the
`XDG Base Directory Specification
<http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_.
Usually, it is ``~/.config/pudb``. The PuDB configuration is stored at
``pudb.cfg`` file inside that directory. Therefore the whole path is usually
``~/.config/pudb/pudb.cfg``.

Following options are available to customise PuDB behaviour:

Line Numbers
************

``line_numbers``

Show or hide the line numbers in the source code pane.

Prompt on quit
**************

``prompt_on_quit``

Prompt or not before quitting.

Shell
*****

``shell``

This is the shell that will be used when you hit ``!``. Available choices:

* internal
* classic
* ipython
* bpython
* ptpython

``custom_shell``

Your own custom shell. See example-shell.py in the pudb distribution. Enter
the full path to a file like it in the box above. ``~`` will be expanded to your
home directory. The file should contain a function called
``pudb_shell(_globals, _locals)`` at the module level.

Theme
*****

``theme``

PuDB UI theme. Available choices:

* classic
* vim
* dark vim
* midnight
* solarized
* agr-256
* monokai
* monokai-256

``custom_theme``

Your own custom theme, see example-theme.py in the pudb distribution. Enter
the full path to a file like it in the box above. ``~`` will be expanded to
your home directory.

Stack Order
*******************

``current_stack_frame``

Show the current stack frame at the top or at the bottom.

Variable Stringifier
********************

``stringifier``

This is the default function that will be called on variables in the variables
list.  Note that you can change this on a per-variable basis by selecting a
variable and hitting Enter or by typing ``t``/``s``/``r``.  Note that str and
repr will be slower than type and have the potential to crash PuDB.

``custom_stringifier``

To use a custom stringifier, see example-stringifier.py in the pudb
distribution. Enter the full path to a file like it in the box above. ``~``
will be expanded to your home directory. The file should contain a function
called ``pudb_stringifier()`` at the module level, which should take a single
argument and return the desired string form of the object passed to it.

Wrap variables
**************

``wrap_variables``

Note that you can change this option on a per-variable basis by selecting the
variable and pressing ``w``.

Display drive
*************

``display``

What driver is used to talk to your terminal. ``raw`` has the most features
(colors and highlighting), but is only correct for XTerm and terminals like it.
``curses`` has fewer features, but it will work with just about any terminal.
``auto`` will attempt to pick between the two based on availability and
the ``$TERM`` environment variable.

Changing this setting requires a restart of PuDB.
