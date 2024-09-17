#! /bin/sh

rsync --verbose --archive --delete _build/html/ doc-upload:doc/pudb
