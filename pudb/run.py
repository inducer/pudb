from __future__ import annotations


COMMAND = {"zsh": "{_command_names -e}"}
PREAMBLE = {
    "zsh": """\
_script_args() {
  # pudb -m <TAB>
  if (($words[(I)-m] == $#words - 1)); then
    _python_modules
  # pudb -m XXX <TAB>
  elif (($words[(I)-m])); then
    _files
  # pudb <TAB>
  else
    _arguments -S -s '(-)1:script_args:_files -g "*.py"' '*: :_files'
  fi
}
""",
}
SCRIPT_ARGS = {"zsh": "_script_args"}


def get_argparse_parser():
    import argparse
    import os
    import sys
    try:
        import shtab
    except ImportError:
        from . import _shtab as shtab

    from pudb import VERSION

    version_info = "%(prog)s v" + VERSION

    if sys.argv[1:] == ["-v"]:
        print(version_info % {"prog": "pudb"})
        sys.exit(os.EX_OK)

    parser = argparse.ArgumentParser(
        "pudb",
        usage="%(prog)s [options] [-m] SCRIPT-OR-MODULE-TO-RUN [SCRIPT_ARGS]",
        epilog=version_info
    )
    shtab.add_argument_to(parser, preamble=PREAMBLE)
    # dest="_continue_at_start" needed as "continue" is a python keyword
    parser.add_argument(
        "-c", "--continue",
        action="store_true",
        dest="_continue_at_start",
        help="Let the script run until an exception occurs or a breakpoint is hit",
    )
    parser.add_argument("-s", "--steal-output", action="store_true")

    # note: we're implementing -m as a boolean flag, mimicking pdb's behavior,
    # and makes it possible without much fuss to support cases like:
    #    python -m pudb -m http.server -h
    # where the -h will be passed to the http.server module
    parser.add_argument("-m", "--module", action="store_true",
                        help="Debug as module or package instead of as a script")

    parser.add_argument("-le", "--log-errors", nargs=1, metavar="FILE",
                        help="Log internal errors to the given file"
                        ).complete = shtab.FILE
    parser.add_argument("--pre-run", metavar="COMMAND",
                        help="Run command before each program run",
                        default="").complete = COMMAND
    parser.add_argument("--version", action="version", version=version_info)
    parser.add_argument("script_args", nargs=argparse.REMAINDER,
                        help="Arguments to pass to script or module"
                        ).complete = SCRIPT_ARGS
    return parser


def main(**kwargs):
    import sys

    parser = get_argparse_parser()

    options = parser.parse_args()
    args = options.script_args

    if options.log_errors:
        from pudb.lowlevel import setlogfile
        setlogfile(options.log_errors[0])

    options_kwargs = {
        "pre_run": options.pre_run,
        "steal_output": options.steal_output,
        "_continue_at_start": options._continue_at_start,
    }

    if len(args) < 1:
        parser.print_help()
        sys.exit(2)

    mainpyfile = args[0]
    sys.argv = args

    if options.module:
        from pudb import runmodule
        runmodule(mainpyfile, **options_kwargs)
    else:
        from os.path import exists
        if not exists(mainpyfile):
            print(f"Error: {mainpyfile} does not exist", file=sys.stderr)
            sys.exit(1)

        from pudb import runscript
        runscript(mainpyfile, **options_kwargs)


if __name__ == "__main__":
    main()
