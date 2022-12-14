import configparser
import os.path

from addict import Dict

from utils.paths import CONF, BASE, BASE_TMP, Paths

Args = Dict()
Args.TASKS = []
Args.ARGSX264 = ''
Args.Suffxies = Dict()

KEY_TOOLS = 'TOOLS'
KEY_PATHS = 'PATHS'
KEY_TemplatePaths = 'TemplatePaths'
KEY_ARGS = 'ARG_TEMPLATES'
KEY_THR = 'ParallelTasks'
KEY_SUF = 'Suffixes'

# for conf assertion
SKIP = ['hint']
_TASK_NAMES = ['1080chs', '1080cht', '720chs', '720cht']

conf = configparser.ConfigParser()


def load_conf():
    defaults = {}

    # default demo
    defaults[KEY_TOOLS] = {
        'ffmpeg': r"D:\Software\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",
        'VSPipe': r"D:\Software\VapourSynth\VapourSynth64Portable\VapourSynth64\VSPipe.exe",
        'x264': r"D:\Software\VapourSynth\VapourSynth64Portable\bin\x264.exe",
        'qaac': r"D:\Software\MeGUI\MeGUI-2913-32\tools\qaac\qaac.exe",
    }
    defaults[KEY_PATHS] = {
        'root_folder': r"D:\animes",
        'hint': r'src\ring.mp3',
    }
    defaults[KEY_TemplatePaths] = {
        '720chs': r'src\template.vpy',
        '720cht': r'src\template.vpy',
        '1080chs': r'src\template.vpy',
        '1080cht': r'src\template.vpy',
    }
    defaults[KEY_ARGS] = {
        'x264': '--demuxer y4m --preset slower --ref 4 --merange 24 --me umh --bframes 10 --aq-mode 3 --aq-strength 0.7 --deblock 0:0 --trellis 2 --psy-rd 0.6:0.1 --crf 21 --output-depth 8 - -o "{VS_TMP}"'
    }
    defaults[KEY_SUF] = {
        'x264_output': '.mp4',
        'merged_output': '.mp4',
    }
    if not os.path.exists(CONF):
        defaults[KEY_THR] = {
            'task1': '1080chs, 1080cht',
            'task2': '720chs, 720cht',
        }
        conf.read_dict(defaults)

        with open(CONF, 'w', encoding='utf8') as f:
            conf.write(f)
        raise FileNotFoundError('已生成配置文件 '+CONF+'\n\n请编辑后重新运行本程序！')
    else:
        conf.read_dict(defaults)
        conf.read(CONF, 'utf8')
        with open(CONF, 'w', encoding='utf8') as f:
            conf.write(f)

    assert_conf()
    try:
        # KEY_TOOLS
        Paths.FFMPEG = conf[KEY_TOOLS]['ffmpeg']
        Paths.VSPIPE = conf[KEY_TOOLS]['VSPipe']
        Paths.X264 = conf[KEY_TOOLS]['x264']

        # KEY_ARGS
        Args.ARGSX264 = conf[KEY_ARGS]['x264']

        # KEY_PATHS
        Paths.ROOT_FOLDER = conf[KEY_PATHS]['root_folder']
        hint = conf[KEY_PATHS]['hint']
        if not hint:
            print('\n关闭提示音')
        else:
            hint = to_abs(hint)
            if os.path.exists(hint):
                Paths.RING = hint.replace('\\', '/')
            else:
                print('\n注意：未找到提示音', hint)

        # KEY_THR
        for _, task in conf[KEY_THR].items():
            joblist = task.split(',')
            joblist = [j.strip() for j in joblist]
            Args.TASKS.append(joblist)

        # KEY_TemplatePaths
        for joblist in Args.TASKS:
            for j in joblist:
                TEMPLATE = conf[KEY_TemplatePaths][j]
                Paths.TemplatePaths[j] = to_abs(TEMPLATE)
                conf[KEY_PATHS]['template'] = Paths.TemplatePaths[j]

        # KEY_SUF
        Args.Suffxies.update(conf[KEY_SUF])

    except KeyError as err:
        raise AssertionError('配置文件结构不完整，请删除'+CONF+'后重新运行本程序！')

def assert_conf():
    # assert config files
    for sec in [KEY_TOOLS, KEY_PATHS]:
        for name, path in conf[sec].items():
            if name not in SKIP:
                assert os.path.exists(path), '错误！无法找到 [' + sec + '] ' + name + ' 路径 '+path+'，请重新配置conf.ini对应项。'
    args = conf[KEY_ARGS]
    assert '"{VS_TMP}"' in args['x264'], '错误！['+KEY_ARGS+'] 中x264参数格式错误，参数-o的值应为"{VS_TMP}" (含引号)。'
    for task in Args.TASKS:
        for j in task:
            assert j in _TASK_NAMES, '错误！['+KEY_THR+'] 中的任务名无法识别，应为 '+', '.join(_TASK_NAMES)+' 中的一种'
    assert 'x264_output' in conf[KEY_SUF] and conf[KEY_SUF]['x264_output'].startswith('.'), '错误！['+KEY_SUF+'] 中的配置错误'
    assert 'merged_output' in conf[KEY_SUF] and conf[KEY_SUF]['merged_output'].startswith('.'), '错误！['+KEY_SUF+'] 中的配置错误'


def to_abs(path):
    if os.path.isabs(path): return path
    abs_ = os.path.join(BASE, path)
    if not os.path.exists(abs_):
        abs_ = os.path.join(BASE_TMP, path)
    return abs_