#!/usr/bin/env python

# This example demonstrates how to debug an mpi4py application.
# Run this with 'mpirun -n 2 python mpi4py-debug.py'.
# You can then attach to the debugger by running 'telnet 127.0.0.1 6899'
# (when using the default pudb configuration) in another terminal.

from mpi4py import MPI
from pudb.remote import debug_remote_on_single_rank


def debugged_function(x):
    y = x + fail  # noqa: F821
    return y


# debug 'debugged_function' on rank 0
debug_remote_on_single_rank(MPI.COMM_WORLD, 0, debugged_function, 42)
