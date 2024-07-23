import configparser
import os.path
from addict import Dict

import utils.consts
from utils.parser import parse_subtaskname
from utils.paths import BASE, BASE_TMP, Paths

Args = Dict(
    TASKS=[],  # type: list[list[str]]
    ARGSX264='',
    ARGSX265='',
    Suffxies={},
    OutPat={},
)

KEY_TOOLS = 'TOOLS'
KEY_PATHS = 'PATHS'
KEY_TemplatePaths = 'TemplatePaths'
KEY_ARGS = 'ARG_TEMPLATES'
KEY_THR = 'ParallelTasks'
KEY_SUF = 'Suffixes'
KEY_OUTPAT = 'OutputPattern'
KEY_DEBUG = 'DEBUG'

# for conf assertion
SKIP = ['hint', 'x264', 'x265']
_RESL_NAMES = ['1080', '720']
_SUBTYPE_NAMES = ['chs', 'cht']
_VENC_NAMES = ['264', '265']

conf = configparser.ConfigParser()


def load_conf(conf_path: str):
    defaults = {}

    # default demo
    defaults[KEY_TOOLS] = {
        'ffmpeg': r"D:\Software\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",
        'mp4box': r"D:\Software\小丸工具箱\xiaowan\tools\mp4box.exe",
        'VSPipe': r"D:\Software\VapourSynth\VapourSynth64Portable\VapourSynth64\VSPipe.exe",
        'x264': r"D:\Software\VapourSynth\VapourSynth64Portable\bin\x264.exe",
        'x265': r"D:\Software\VapourSynth\VapourSynth64Portable\bin\x265.exe",
    }
    defaults[KEY_PATHS] = {
        'root_folder': r"D:\animes",
        'hint': r'src\ring.mp3',
    }
    defaults[KEY_TemplatePaths] = {
        '720chs264': r'src\template.vpy',
        '720cht264': r'src\template.vpy',
        '1080chs264': r'src\template 2023-11_1080P.vpy',
        '1080cht264': r'src\template 2023-11_1080P.vpy',
        '720chs265': r'src\template.vpy',
        '720cht265': r'src\template.vpy',
        '1080chs265': r'src\template 2023-11_1080P.vpy',
        '1080cht265': r'src\template 2023-11_1080P.vpy',
        '720chs264_noass': r'src\template_noass.vpy',
        '720cht264_noass': r'src\template_noass.vpy',
        '720chs265_noass': r'src\template_noass.vpy',
        '720cht265_noass': r'src\template_noass.vpy',
    }
    defaults[KEY_ARGS] = {
        'x264': '--demuxer y4m --preset veryslow --ref 8 --merange 24 --me umh --bframes 10 --aq-mode 3 --aq-strength 0.7 --deblock 0:0 --trellis 2 --psy-rd 0.6:0.1 --crf 18.5 --output-depth 8 - -o "{VS_TMP}"',
        'x265': '--y4m --preset slower --frame-threads 1 --deblock -1:-1 --ctu 32 --crf 16.0 --pbratio 1.2 --cbqpoffs -2 --crqpoffs -2 --no-sao --me 3 --subme 3 --merange 44 --b-intra --no-rect --no-amp --ref 4 --weightb --keyint 360 --min-keyint 1 --bframes 6 --aq-mode 1 --aq-strength 0.8 --rd 4 --psy-rd 2.0 --psy-rdoq 3.0 --no-open-gop --rc-lookahead 80 --scenecut 40 --qcomp 0.65 --no-strong-intra-smoothing --vbv-bufsize 30000 --vbv-maxrate 28000 --output-depth 10 - -o "{VS_TMP}"',
    }
    defaults[KEY_SUF] = {
        'x264_vs_output': '.mp4',
        'x264_merged_output': '.mp4',
        'x265_vs_output': '.hevc',
        'x265_merged_output': '.hevc',
    }
    defaults[KEY_OUTPAT] = {
        'folder': '[Yumezukuri] {NAME} [{EP_EN}]',
        'file': '[Yumezukuri] {NAME} [{EP_EN}] [{VTYPE}-{BIT}bit {RESL}P] [{LANG_EN}] [{VER}]',
    }
    defaults[KEY_DEBUG] = {
        'purge_tmpfile': 'true'
    }
    if not os.path.exists(conf_path):
        defaults[KEY_THR] = {
            'task1': '1080chs265, 1080cht265',
            'task2': '720chs264, 720cht264',
        }
        conf.read_dict(defaults)

        with open(conf_path, 'w', encoding='utf8') as f:
            conf.write(f)
        raise FileNotFoundError('已生成配置文件至 '+conf_path+'\n\n请编辑后重新运行本程序！')
    else:
        conf.read_dict(defaults)
        conf.read(conf_path, 'utf8')
        with open(conf_path, 'w', encoding='utf8') as f:
            conf.write(f)

    assert_conf()
    # load from conf
    try:
        # KEY_TOOLS
        Paths.FFMPEG = conf[KEY_TOOLS]['ffmpeg']
        Paths.MP4BOX = conf[KEY_TOOLS]['mp4box']
        Paths.VSPIPE = conf[KEY_TOOLS]['VSPipe']
        Paths.X264 = conf[KEY_TOOLS]['x264']
        Paths.X265 = conf[KEY_TOOLS]['x265']

        # KEY_ARGS
        Args.ARGSX264 = conf[KEY_ARGS]['x264']
        Args.ARGSX265 = conf[KEY_ARGS]['x265']

        # KEY_PATHS
        Paths.ROOT_FOLDER = conf[KEY_PATHS]['root_folder']
        hint = conf[KEY_PATHS]['hint']
        if hint:
            hint = to_abs(hint)
            if os.path.exists(hint):
                Paths.RING = hint.replace('\\', '/')
            else:
                print('\n注意：未找到提示音', hint)

        # KEY_THR
        for _, task in conf[KEY_THR].items():
            subtasks = task.split(',')
            subtasks = [s.strip() for s in subtasks]
            Args.TASKS.append(subtasks)

        # KEY_TemplatePaths
        for j in conf[KEY_TemplatePaths].keys():
            Paths.TemplatePaths[j] = to_abs(conf[KEY_TemplatePaths][j])

        # KEY_SUF
        Args.Suffxies.update(conf[KEY_SUF])
        # KEY_OUTPAT
        Args.OutPat.update(conf[KEY_OUTPAT])

        utils.consts.PURGETMP = conf[KEY_DEBUG].getboolean('purge_tmpfile')

        assert_conf_post()

    except KeyError as err:
        raise AssertionError('配置文件结构不完整，请删除'+conf_path+'后重新运行本程序！')

    return conf

def assert_conf():
    # assert config files
    for sec in [KEY_TOOLS, KEY_PATHS]:
        for name, path in conf[sec].items():
            if name not in SKIP:
                assert os.path.exists(path), '错误！无法找到 [' + sec + '] ' + name + ' 路径 '+path+'，请重新配置conf.ini对应项。'
    try:
        assert 'purge_tmpfile' in conf[KEY_DEBUG]
        conf[KEY_DEBUG].getboolean('purge_tmpfile')
    except (AssertionError, ValueError):
        raise AssertionError('错误！['+KEY_DEBUG+']中的配置错误')


def assert_conf_post():
    _TASK_NAMES = [f"{resl}{subtype}{venc}" for resl in _RESL_NAMES for subtype in _SUBTYPE_NAMES for venc in _VENC_NAMES]
    need264 = False
    need265 = False
    for task in Args.TASKS:
        if need264 and need265: break
        for s in task:
            assert s in _TASK_NAMES, '错误！[' + KEY_THR + '] 中的任务名无法识别，应为 ' + ', '.join(_TASK_NAMES) + ' 中的一种'
            assert os.path.exists(conf[KEY_TemplatePaths][s]), '错误！无法找到 ['+KEY_TemplatePaths+'] 中的 ' + s + ' 项，路径'+conf[KEY_TemplatePaths][s]+'，请重新配置conf.ini对应项。'

            _, _, venc, _ = parse_subtaskname(s)
            if venc.is264():
                need264 = True
            if venc.is265():
                need265 = True

    args = conf[KEY_ARGS]
    if need264:
        assert os.path.exists(conf[KEY_TOOLS]['x264']), '错误！无法找到' + KEY_TOOLS + '] x264 路径 ' + conf[KEY_TOOLS]['x264'] + '，请重新配置conf.ini对应项。'
        assert '"{VS_TMP}"' in args['x264'], '错误！[' + KEY_ARGS + '] 中x264参数格式错误，参数-o的值应为"{VS_TMP}" (含引号)。'
        assert 'x264_merged_output' in conf[KEY_SUF] and conf[KEY_SUF]['x264_merged_output'].startswith('.'), '错误！[' + KEY_SUF + '] 中的配置错误'
        assert 'x264_vs_output' in conf[KEY_SUF] and conf[KEY_SUF]['x264_vs_output'].startswith('.'), '错误！[' + KEY_SUF + '] 中的配置错误'
    if need265:
        assert os.path.exists(conf[KEY_TOOLS]['x265']), '错误！无法找到' + KEY_TOOLS + '] x265 路径 ' + conf[KEY_TOOLS]['x265'] + '，请重新配置conf.ini对应项。'
        assert '"{VS_TMP}"' in args['x265'], '错误！[' + KEY_ARGS + '] 中x265参数格式错误，参数-o的值应为"{VS_TMP}" (含引号)。'
        assert 'x265_vs_output' in conf[KEY_SUF] and conf[KEY_SUF]['x265_vs_output'].startswith('.'), '错误！[' + KEY_SUF + '] 中的配置错误'
        assert 'x265_merged_output' in conf[KEY_SUF] and conf[KEY_SUF]['x265_merged_output'].startswith('.'), '错误！[' + KEY_SUF + '] 中的配置错误'
    return need264, need265

def to_abs(path):
    if os.path.isabs(path): return path
    abs_ = os.path.join(BASE, path)
    if not os.path.exists(abs_):
        abs_ = os.path.join(BASE_TMP, path)
    return abs_