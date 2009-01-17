#!/usr/bin/env python
# Contributor : mathieu.clabaut@gmail.com
# License : GPL v3

import mpdclient2, re, random, sys,os, time
import logging
from optparse import OptionParser
import daemon

try:
    import optcomplete
    has_optcomplete = True
except ImportError:
    has_optcomplete = False
LOG_FILENAME = '/tmp/mpdrandomd.log'
parser = OptionParser( version="0.1",
        usage="%prog [options]"
        "\n\n\tFeed an mpd daemon with a randomize playlist")
parser.add_option(  "-k", "--keep",
                    action="store", type="int", dest="keep", 
		    default=100,
		    metavar="NB",
                    help="how many songs already played are keeped")
parser.add_option(  "-n", "--enqueue",
                    action="store", type="int", dest="enqueue", 
		    default=2,
		    metavar="NB",
                    help="how many songs to enqueue before the one playing")
parser.add_option(  "--daemon",
                    action="store_const", const=True, dest="daemon", 
		    default=False,
                    help="output debug information to stderr")
parser.add_option(  "--no-update",
                    action="store_const", const=False, dest="update", 
		    default=True,
                    help="do not update the database on startup")
parser.add_option(  "--clear",
                    action="store_const", const=True, dest="clear", 
		    default=False,
                    help="emtpy mpd database on startup")
parser.add_option(  "-x", "--exclude-regex",
                    action="append", type="string", dest="exclude", 
		    default=[],
		    metavar="REGEX",
                    help="Regex against which matching files will be excluded")
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
parser.add_option(  "--music-dir",
                    action="store", type="string", dest="musicdir", 
		    default=None,
		    metavar="DIR",
                    help="MPD music directory (default from mpd.conf)")
parser.add_option(  "-c","--mpd-conf",
                    action="store", type="string", dest="mpdconf", 
		    default="/etc/mpd.conf",
		    metavar="FILE",
                    help="MPD conf file (default /etc/mpd.conf")
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
		    default=LOG_FILENAME,
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


class RetryMPDConnection(mpdclient2.mpd_connection):
    def __init__(self,host,port,password):
	self.host=host
	self.port=port
	self.password=password
	mpdclient2.mpd_connection.__init__(self, host, port)
	if password != '':
	    self.password(password)


class RandomPlayList():
    def __init__(self, nb_keeped=5, nb_queued=2, doupdate=True, doclear=False,  host='localhost', port=6600, passwd='', musicdir="/home/music", mpdconf="/etc/mpd.conf", exclude=[]):
	self.mpdconf = mpdconf
	self.musicdir=self.init_music_dir(musicdir)
	logging.debug("Exclude regex : %s" % '|'.join(exclude))
	self.except_re=re.compile('|'.join(exclude))
	#r'Enfants/|soirees/|\.m3u')
	self.path_re=re.compile(r'(.*)/[^/]*')
	self.nb_keeped = nb_keeped
	self.nb_queued = nb_queued
	self.doclear = doclear
	self.c = self.connect(host, port, passwd)
	if doupdate:
	    self.update_db()

	self.c.random(0)
	#self.c.play()

    def init_music_dir(self, musicdir):
	if musicdir is None:
	    re_musicdir=re.compile(r"""^\s*music_directory\s*["']([^"']*)["']""")
	    res=None
	    with open(self.mpdconf, 'r') as f: 
		for line in f:
		    res=re_musicdir.match(line)
		    if res:
			break
	    if res is not None:
		res = res.group(1)
		logging.debug("Music directory %s (from %s)" % (res,self.mpdconf))
		return  res
	else:
	    raise RuntimeError("No music directory specified or found")

    def connect(self,  host, port, passwd):
	c = None
	while c is None:
	    try:
		c = RetryMPDConnection(host,port,passwd)
	    except Exception,e:
		logging.info("Failed to connect to mpd")
		logging.debug(e)
		c = None
		time.sleep(3)
	return c


    def norandom_is_in_path(self, file):
	found=False
	while '/' in file and not found:
	    file=self.path_re.match(file).group(1)
	    norandompath = "%s/%s/%s" % (self.musicdir,file,"norandom")
	    found = os.path.lexists(norandompath)
	if found:
	    return file
	else:
	    return None

    def update_db(self):
	self.c.update()
	logging.info( "Updating db",)
	while 'updating_db' in self.c.status():
	    time.sleep(1)
	logging.info( "Done")

    def delete_old_songs(self, pos):
	if pos > self.nb_keeped:
	    logging.debug("Delete first %d songs" % (pos - self.nb_keeped))
	    for i in xrange(pos - self.nb_keeped, 0, -1):
		self.c.delete(i)


    def enqueue_new_songs(self, pos, length):
	if length - pos > self.nb_queued:
	    return
	to_be_added = self.nb_queued - length + pos + 1
	added = 0
	while  added < to_be_added:
	    added += self.enqueue_one_song_or_album()
	logging.debug("Enqued %d songs (%d required)" % (added,to_be_added))


    def get_next_song_index(self):
	nb_songs=len(self.songs)
	choosen = random.randrange(0,nb_songs)
	# get another song if the random one is in the current playlist or
	# match except_re
	while (self.songs[choosen] in self.pl_songs or self.except_re.match(self.songs[choosen].file)):
	    choosen = random.randrange(0,nb_songs)
	    if self.except_re.match(self.songs[choosen].file):
		self.songs.pop(choosen)
	return choosen
    
    def enqueue_one_song_or_album(self):
	self.pl_songs = filter(lambda x: 'file' in x, self.c.playlistinfo())
	choosen = self.get_next_song_index()
	file = self.songs[choosen].file
	if '/' in file:
	    path = self.norandom_is_in_path(file)
	    if path is not None:
		logging.debug("No Random : "+path )
		album = filter(lambda x: x.file.find(path)==0, self.songs)
		album.sort(key=lambda x:x.file)
		logging.debug ("Enqueue one album : %s" % path)
		for s in album:
		    self.c.add(s.file)
		return len(album)
	    else:
		logging.debug("Enqueue one song : %s" % file)
		self.c.add(file)
		return 1
	else:
	    logging.debug("Enqueue one song : %s" % file)
	    self.c.add(file)
	    return 1



    def feed_mpd(self):
	if self.doclear:
	    self.c.clear()
	self.songs = filter(lambda x: 'file' in x, self.c.listallinfo())

	wasplaying = self.c.status().state == 'play'

	while True:
	    playlist_len = int(self.c.status().playlistlength)
	    if playlist_len == 0:
		self.enqueue_new_songs(0,0)
		playlist_len = int(self.c.status().playlistlength)
	    if 'song' in  self.c.status():
		pos = int(self.c.status().song)
	    else:
		pos = 0
	    self.delete_old_songs(pos)
	    self.enqueue_new_songs(pos,playlist_len)
	    #curlen = int(self.c.currentsong().time)
	    #curtime = int(self.c.status().time.split(':')[0])
	    #sleep(curlen-curtime + 3)
	    time.sleep(3)

		



class UsageError(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    global options
    if argv is None:
        argv = sys.argv
    (options, args) = parser.parse_args()
    if options.daemon:
	daemon.createDaemon()
    loggerInit(options)
    while True:
	try:
	    r=RandomPlayList(doupdate=options.update, doclear=options.clear,
		    nb_keeped=options.keep, nb_queued=options.enqueue,
		    host=options.host, passwd=options.password,
		    port=options.port, mpdconf=options.mpdconf,
		    musicdir=options.musicdir, exclude=options.exclude)
	    r.feed_mpd()
	except Exception,e:
	    logging.debug(e)

if __name__ == "__main__":
    sys.exit(main())
# vim: se sw=4 sts=4 et:
