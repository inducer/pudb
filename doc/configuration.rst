Configuration
-------------

Following options are available to customise PuDB behaviour:

shell
*****

This is the shell that will be used when you hit ``!``. Available choices:

* internal
* classic
* ipython
* bpython
* ptpython

theme
*****

PuDB UI theme. Select one available or use your own by setting ``custom_theme``.

custom_theme
************

To use a custom theme, see example-theme.py in the pudb distribution. Enter
the full path to a file like it in the box above. ``~`` will be expanded to
your home directory. Note that a custom theme will not be applied until you
close this dialog.


line_numbers
************

Show or hide the line numbers in the source code pane.

sidebar_width
*************

The sidebar pane width.

variables_weight
****************

The variables pane height.

stack_weight
************

The stack pane height.

breakpoints_weight
******************

The breakpoints pane height.

current_stack_frame
*******************

Show the current stack frame at the top or at the bottom.

stringifier
***********

This is the default function that will be called on variables in the variables
list.  Note that you can change this on a per-variable basis by selecting a
variable and hitting Enter or by typing ``t``/``s``/``r``.  Note that str and
repr will be slower than type and have the potential to crash PuDB.

custom_stringifier
******************

To use a custom stringifier, see example-stringifier.py in the pudb
distribution. Enter the full path to a file like it in the box above. ``~``
will be expanded to your home directory. The file should contain a function
called ``pudb_stringifier()`` at the module level, which should take a single
argument and return the desired string form of the object passed to it. Note
that if you choose a custom stringifier, the variables view will not be updated
until you close this dialog.

wrap_variables
**************

Note that you can change this option on a per-variable basis by selecting the
variable and pressing ``w``.

display
*******

What driver is used to talk to your terminal. ``raw`` has the most features
(colors and highlighting), but is only correct for XTerm and terminals like it.
``curses`` has fewer features, but it will work with just about any terminal.
``auto`` will attempt to pick between the two based on availability and
the ``$TERM`` environment variable.

Changing this setting requires a restart of PuDB.

prompt_on_quit
**************

Prompt or not before quitting.