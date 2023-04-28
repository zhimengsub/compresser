import os.path
import sys

from addict import Dict

Paths = Dict(
    RING='',
    ROOT_FOLDER='',
    FFMPEG='',
    QAAC='',
    VSPIPE='',
    X264='',
    TemplatePaths = {
        '720chs': '',
        '720cht': '',
        '1080chs': '',
        '1080cht': '',
        '720chs_noass': '',
        '720cht_noass': '',
        'audio': '',
    }
)

ISEXE = hasattr(sys, 'frozen')
BASE = os.path.dirname(sys.executable if ISEXE else os.path.dirname(__file__))  # exe/py所在路径
BASE_TMP = sys._MEIPASS if ISEXE else BASE  # 打包后运行时系统tmp所在路径，或py所在路径
SRC = os.path.join(BASE_TMP, 'src')
TMP = os.path.join(BASE, 'tmp')
os.makedirs(TMP, exist_ok=True)
LOG = os.path.join(BASE, 'log')
os.makedirs(LOG, exist_ok=True)
CONF = os.path.join(BASE, 'conf.ini')

