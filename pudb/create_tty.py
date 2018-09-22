from __future__ import absolute_import, division, print_function

import errno
import subprocess as subp


def main():
    try:
        subp.call(['tmux', 'new', 'echo -n "Set PUDB_TTY to: "; tty; perl -MPOSIX -e pause'])
    except OSError as e:
        if e.errno == errno.ENOENT:
            print('Error: this script requires tmux to be installed and in PATH')
        else:
            raise


if __name__ == '__main__':
    main()
