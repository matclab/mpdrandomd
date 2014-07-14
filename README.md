# mpdrandomd #
Small daemon written in python that lively enqueues new songs or albums in the
current mpd playlist (only n songs or 1 album in advance). Album whose
directory contains a file name `norandom` are always added in one time and in
order.
Also provides a `mpdalbumnow.py` script which complete the current song
with the end of the album.

## Requirements ##

Depends on python2 and python-mpdclient2 library.

## Install ##

Can be download there http://bitbucket.org/matclab/mpdrandomd/src/ (or cloned
with mercurial : `hg clone https://bitbucket.org/matclab/mpdrandomd/` or cloned
from git : `https://github.com/matclab/mpdrandomd.git`)


## Usage ##
```
   Usage: mpdrandomd.py [options]

      Feed an mpd daemon with a randomize playlist

   Options:
   --version             show program's version number and exit
   -h, --help            show this help message and exit
   -k NB, --keep=NB      how many songs already played are keeped
   -n NB, --enqueue=NB   how many songs to enqueue before the one playing
   --daemon              output debug information to stderr
   --no-update           do not update the database on startup
   --clear               emtpy mpd database on startup
   -x REGEX, --exclude-regex=REGEX
                         Regex against which matching files will be excluded
   -H NAME, --host=NAME  MPD host
   -P NB, --port=NB      MPD port
   --password=PWD        MPD connexion password
   --music-dir=DIR       MPD music directory (default from mpd.conf)
   -c FILE, --mpd-conf=FILE
                         MPD conf file (default /etc/mpd.conf
   -q, --quiet           don't print status messages to stderr
   -v, --verbose         output verbose status to stderr
   -d, --debug           output debug information to stderr
   -l FILE, --log-file=FILE
                         log file (default /tmp/mpdrandomd.log, '-' for stderr)
```

## Author ##
mathieu.clabaut@gmail.com
