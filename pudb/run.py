from __future__ import absolute_import, division, print_function


def main():
    import sys

    from optparse import OptionParser
    parser = OptionParser(
            usage="usage: %prog [options] [SCRIPT-TO-RUN|-m MODULE] [ARGUMENTS]")

    parser.add_option("-s", "--steal-output", action="store_true"),
    parser.add_option("-m", "--module", metavar="MODULE",
                      help="Debug module or package instead of script"),
    parser.add_option("--pre-run", metavar="COMMAND",
            help="Run command before each program run",
            default="")
    parser.disable_interspersed_args()
    options, args = parser.parse_args()

    options_kwargs = {
        'pre_run': options.pre_run,
        'steal_output': options.steal_output,
    }

    if options.module:
        sys.argv = args
        from pudb import runmodule
        runmodule(options.module, **options_kwargs)
    else:
        if len(args) < 1:
            parser.print_help()
            sys.exit(2)

        mainpyfile = args[0]

        from os.path import exists
        if not exists(mainpyfile):
            print('Error: %s does not exist' % mainpyfile)
            sys.exit(1)

        sys.argv = args

        from pudb import runscript
        runscript(mainpyfile, **options_kwargs)


if __name__ == '__main__':
    main()
