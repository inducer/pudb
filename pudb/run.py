def main():
    import sys

    from optparse import OptionParser
    parser = OptionParser(
            usage="usage: %prog [options] SCRIPT-TO-RUN [SCRIPT-ARGUMENTS]")

    parser.add_option("-s", "--steal-output", action="store_true"),
    parser.add_option("--pre-run", metavar="COMMAND",
            help="Run command before each program run",
            default="")
    parser.disable_interspersed_args()
    options, args = parser.parse_args()

    if len(args) < 1:
        parser.print_help()
        sys.exit(2)

    mainpyfile =  args[0]
    from os.path import exists, dirname
    if not exists(mainpyfile):
        print 'Error:', mainpyfile, 'does not exist'
        sys.exit(1)

    sys.argv = args

    from pudb import runscript
    runscript(mainpyfile, 
            pre_run=options.pre_run, 
            steal_output=options.steal_output)




if __name__=='__main__':
    main()

