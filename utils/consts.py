import sys

# for debug
DEBUG = hasattr(sys, 'gettrace') and sys.gettrace() is not None
DEBUGMODE = False
SKIPAUD = False
SKIPVSTMP = False
PURGETMP = True
PAUSE = True

videosuffs = ['mkv', 'mp4']
