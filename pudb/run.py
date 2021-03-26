def main():
    import sys

    import argparse
    parser = argparse.ArgumentParser(
        usage="%(prog)s [options] [-m] SCRIPT-OR-MODULE-TO-RUN [SCRIPT_ARGS]"
    )
    parser.add_argument("-s", "--steal-output", action="store_true"),

    # note: we're implementing -m as a boolean flag, mimicking pdb's behavior,
    # and makes it possible without much fuss to support cases like:
    #    python -m pudb -m http.server -h
    # where the -h will be passed to the http.server module
    parser.add_argument("-m", "--module", action="store_true",
                        help="Debug as module or package instead of as a script")

    parser.add_argument("-le", "--log-errors", nargs=1, metavar="FILE",
                        help="Log internal errors to the given file")
    parser.add_argument("--pre-run", metavar="COMMAND",
                        help="Run command before each program run",
                        default="")
    parser.add_argument("script_args", nargs=argparse.REMAINDER,
                        help="Arguments to pass to script or module")

    options = parser.parse_args()
    args = options.script_args

    if options.log_errors:
        from pudb.lowlevel import setlogfile
        setlogfile(options.log_errors[0])

    options_kwargs = {
        "pre_run": options.pre_run,
        "steal_output": options.steal_output,
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
            print("Error: %s does not exist" % mainpyfile, file=sys.stderr)
            sys.exit(1)

        from pudb import runscript
        runscript(mainpyfile, **options_kwargs)


if __name__ == "__main__":
    main()
