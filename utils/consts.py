import sys

# for debug
DEBUG = hasattr(sys, 'gettrace') and sys.gettrace() is not None
DEBUGMODE = DEBUG or False
USETESTFOLDER = DEBUGMODE or False
SKIPAUD = DEBUGMODE or False
SKIPVSTMP = DEBUGMODE or False
PURGETMP = DEBUGMODE or True
PAUSE = True

videosuffs = ['mkv', 'mp4']
