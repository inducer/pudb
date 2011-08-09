#!/usr/bin/env python
"""
This file shows how you can define a custom stringifier for PuDB.

A stringifier is a function that is called on the variables in the namespace
for display in the variables list.  The default is type()*, as this is fast and
cannot fail.  PuDB also includes built-in options for using str() and repr().

Note that str() and repr() will be slower than type(), which is especially
noticable when you have many varialbes, or some of your variables have very
large string/repr representations.

Also note that if you just want to change the type for one or two variables,
you can do that by selecting the variable in the variables list and pressing
Enter, or by pressing t, s, or r.

To define a custom stringifier, create a file like this one with a function
called pudb_stringifier() at the module level.  pudb_stringifier(obj) should
return a string value for an object (note that str() will always be called on
the result). Note that the file will be execfile'd.

Then, go to the PuDB preferences window (type Ctrl-p inside of
PuDB), and add the path to the file in the "Custom" field under the "Variable
Stringifier" heading.

The example in this file returns the string value, unless it take more than 500
ms (1 second in Python 2.5-) to compute, in which case it falls back to the
type.

TIP: Run "python -m pudb.run example-stringifier.py and set this file to be
your stringifier in the settings to see how it works.

You can use custom stringifiers to do all sorts of things: callbacks, custom
views on variables of interest without having to use a watch variable or the
expanded view, etc.

* - Actually, the default is a mix between type() and str().  str() is used for
    a handful of "safe" types for which it is guaranteed to be fast and not to
    fail.
"""
import time
import signal
import sys
import math

class TimeOutError(Exception):
    pass

def timeout(signum, frame, time):
    raise TimeOutError("Timed out after %d seconds" % time)

def run_with_timeout(code, time, globals=None):
    """
    Evaluate ``code``, timing out after ``time`` seconds.

    In Python 2.5 and lower, ``time`` is rounded up to the nearest integer.
    The return value is whatever ``code`` returns.
    """
    # Set the signal handler and a ``time``-second alarm
    signal.signal(signal.SIGALRM, lambda s, f: timeout(s, f, time))
    if sys.version_info > (2, 5):
        signal.setitimer(signal.ITIMER_REAL, time)
    else:
        # The above only exists in Python 2.6+
        # Otherwise, we have to use this, which only supports integer arguments
        # Use math.ceil to round a float up.
        time = int(math.ceil(time))
        signal.alarm(time)
    r = eval(code, globals)
    signal.alarm(0)          # Disable the alarm
    return r

def pudb_stringifier(obj):
    """
    This is the custom stringifier.

    It returns str(obj), unless it take more than a second to compute,
    in which case it falls back to type(obj).
    """
    try:
        return run_with_timeout("str(obj)", 0.5, {'obj':obj})
    except TimeOutError:
        return (type(obj), "(str too slow to compute)")

# Example usage

class FastString(object):
    def __str__(self):
        return "This was fast to compute."

class SlowString(object):
    def __str__(self):
        time.sleep(10) # Return the string value after ten seconds
        return "This was slow to compute."

fast = FastString()
slow = SlowString()

# If you are running this in PuDB, set this file as your custom stringifier in
# the prefs (Ctrl-p) and run to here. Notice how fast shows the string value,
# but slow shows the type, as the string value takes too long to compute.
