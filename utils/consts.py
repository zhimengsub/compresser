import sys

sysargs = {}

# for debug
DEBUG = hasattr(sys, 'gettrace') and sys.gettrace() is not None
DEBUGMODE = DEBUG or False
USETESTFOLDER = DEBUGMODE
SKIPAUD = DEBUGMODE or False
SKIPVSTMP = DEBUGMODE or False
PURGETMP = not DEBUGMODE
PAUSE = True

videosuffs = ['mkv', 'mp4', 'm2ts']
