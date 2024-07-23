import os.path
import sys

from addict import Dict

Paths = Dict(
    RING='',
    ROOT_FOLDER='',
    FFMPEG='',
    MP4BOX='',
    VSPIPE='',
    X264='',
    X265='',
    TemplatePaths={}
)

ISEXE = hasattr(sys, 'frozen')
BASE = os.path.dirname(sys.executable if ISEXE else os.path.dirname(__file__))  # exe/py所在路径
BASE_TMP = sys._MEIPASS if ISEXE else BASE  # 打包后运行时系统tmp所在路径，或py所在路径
SRC = os.path.join(BASE_TMP, 'src')
TMP = os.path.join(BASE, 'tmp')
os.makedirs(TMP, exist_ok=True)
LOG = os.path.join(BASE, 'log')
os.makedirs(LOG, exist_ok=True)

