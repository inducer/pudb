#!/usr/bin/env python

from mpi4py import MPI
from pudb.remote import debug_remote_on_single_rank


def debugged_function(x):
    y = x + fail  # noqa: F821
    return y


# debug this application on rank 0
debug_remote_on_single_rank(MPI.COMM_WORLD, 0, debugged_function, 42)
