import os
import sys
from urllib.request import urlopen


_conf_url = \
        "https://raw.githubusercontent.com/inducer/sphinxconfig/main/sphinxconfig.py"
with urlopen(_conf_url) as _inf:
    exec(compile(_inf.read(), _conf_url, "exec"), globals())

sys.path.insert(0, os.path.abspath(".."))

copyright = "2017-21, Andreas Kloeckner and contributors"
author = "Andreas Kloeckner and contributors"

ver_dic = {}
with open("../pudb/__init__.py") as ver_file:
    ver_src = ver_file.read()
exec(compile(ver_src, "../pudb/__init__.py", "exec"), ver_dic)
version = ver_dic["VERSION"]

# The full version, including alpha/beta/rc tags.
release = version

intersphinx_mapping = {
        "python": ("https://docs.python.org/3", None),
        "urwid": ("https://urwid.org/", None),
        "mpi4py": ("https://mpi4py.readthedocs.io/en/stable/", None),
        }


sphinxconfig_missing_reference_aliases = {
    "MPI.Intracomm": "obj:mpi4py.MPI.Intracomm",
}


nitpick_ignore_regex = [
    ["py:class", r"P"],
    ["py:class", r"P.args"],
    ["py:class", r"P.kwargs"],
    ["py:class", r"ResultT"],
    ["py:class", r"FrameType"],
    ["py:class", r"TracebackType"],
    ["py:class", r"OptExcInfo"],
]


def setup(app) -> None:
    app.connect("missing-reference", process_autodoc_missing_reference)  # noqa: F821
