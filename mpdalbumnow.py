#!/usr/bin/env python
# Contributor : mathieu.clabaut@gmail.com
# License : GPL v3

import mpdclient2, sys,os, re
import logging
from optparse import OptionParser

try:
    import optcomplete
    has_optcomplete = True
except ImportError:
    has_optcomplete = False
LOG_FILENAME = '/tmp/mpdalbumnow.log'
parser = OptionParser( version="0.1",
        usage="%prog [options]"
        "\n\n\tcomplete the playlist after the current song, with the current album")
password, host = mpdclient2.parse_host(os.environ.get('MPD_HOST', 'localhost'))
parser.add_option(  "-H", "--host",
                    action="store", type="string", dest="host", 
		    default=host,
		    metavar="NAME",
                    help="MPD host")
parser.add_option(  "-P", "--port",
                    action="store", type="int", dest="port", 
		    default=int(os.environ.get('MPD_PORT', 6600)),
		    metavar="NB",
                    help="MPD port")
parser.add_option(   "--password",
                    action="store", type="string", dest="password", 
		    default=password,
		    metavar="PWD",
                    help="MPD connexion password")
parser.set_defaults(verbose=logging.WARNING)
parser.add_option("-q", "--quiet",
                    action="store_const", const=logging.CRITICAL, dest="verbose", 
                    help="don't print status messages to stderr")
parser.add_option("-v", "--verbose",
                    action="store_const", const=logging.INFO, dest="verbose", 
                    help="output verbose status to stderr")
parser.add_option("-d", "--debug",
                    action="store_const", const=logging.DEBUG, dest="verbose", 
                    help="output debug information to stderr")
parser.add_option(  "-l","--log-file",
                    action="store", type="string", dest="logfile", 
		    default='-',
		    metavar="FILE",
                    help="log file (default %s, '-' for stderr)" % LOG_FILENAME)


if has_optcomplete:
    optcomplete.autocomplete(parser)

def loggerInit(opt):
    if opt.logfile == '-':
	logging.basicConfig(level=opt.verbose,format="%(levelname)-8s %(message)s")
    else:
	logging.basicConfig(filename = opt.logfile, level=opt.verbose,format="%(asctime)s-%(levelname)-8s %(message)s")

def Print(verb, str):
    """Print 'str' to stderr if 'verb' is below the current verbosity level"""
    if verb <= options.verbose:
        sys.stderr.write(str)


def insertalbum(options):
    c=mpdclient2.connect(host=options.host, port=options.port, passwd=options.password)
    cur=c.currentsong()
    if '/' in cur.file:
        path_re=re.compile(r'^(.*)/([^/]*)$')
        path,file=path_re.match(cur.file).group(1,2)
        songs = filter(lambda x: 'file' in x, c.listallinfo())
        album = filter(lambda x: x.file.find(path) == 0, songs)
        album.sort(key=lambda x:x.file,reverse=True)
        seen=False
        last=int(c.status().playlistlength)
        for s in album:
            if s.file == cur.file:
                seen=True
            if not seen:
                logging.debug("add %s" % s.file)
                c.add(s.file)
                c.move(last,int(cur.pos)+1)
                last+=1


def main(argv=None):
    global options
    if argv is None:
        argv = sys.argv
    (options, args) = parser.parse_args()
    loggerInit(options)
    insertalbum(options)

if __name__ == "__main__":
    sys.exit(main())
# vim : se sw=4 sts=4 et



# vim : se sw=4 sts=4 et
