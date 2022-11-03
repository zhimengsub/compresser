import enum
import re
import sys
import os
import configparser
import subprocess
import threading
from subprocess import PIPE, CalledProcessError
import traceback
import time
from datetime import timedelta
from playsound import playsound
from zhconv import convert as convlang

VER = 'v2.0.3'
DESCRIPTION = '************************************************************************************\n' + \
              '* 织梦字幕组自动压制工具\n' + \
              '* —— ' + VER + ' by 谢耳朵w\n*\n' + \
              '* 使用说明、获取最新版本、提交建议和错误请前往 https://github.com/zhimengsub/compresser\n' + \
              '************************************************************************************'

ISEXE = hasattr(sys, 'frozen')
BASE = os.path.dirname(sys.executable if ISEXE else __file__)  # exe/py所在路径
BASE_TMP = sys._MEIPASS if ISEXE else BASE  # 打包后运行时系统tmp所在路径，或py所在路径
SRC = os.path.join(BASE_TMP, 'src')
TEMPLATE = ''
RING = ''
TMP = os.path.join(BASE, 'tmp')
os.makedirs(TMP, exist_ok=True)
SCRIPT_TMP = os.path.join(TMP, 'script.vpy')
TASKS = []
M4A_TMP = '' # os.path.join(TMP, f'{invidname_noext}_m4a.m4a')
VS_TMP = '' # os.path.join(TMP, f'{invidname_noext}_vs.mp4')
FFMPEG = ''
VSPIPE = ''
X264 = ''
CONF = os.path.join(BASE, 'conf.ini')
ARGSX264 = ''

ROOT_FOLDER = ''

KEY_TOOLS = 'TOOLS'
KEY_PATHS = 'PATHS'
KEY_ARGS = 'ARG_TEMPLATES'
KEY_THR = 'ParallelTasks'

# for conf assertion
SKIP = ['hint']
_TASK_NAMES = ['1080chs', '1080cht', '720chs', '720cht']

# for debug
DEBUG = hasattr(sys, 'gettrace') and sys.gettrace() is not None
DEBUGMODE = False
SKIPAUD = False
SKIPVSTMP = False
PURGETMP = True
PAUSE = True

conf = configparser.ConfigParser()
videosuffs = ['mkv', 'mp4']

def log(*args, prefix='', **kwargs):
    t = '['+time.strftime('%H:%M:%S', time.localtime())+']'
    print()
    if prefix:
        print(t, prefix, *args, **kwargs)
    else:
        print(t, *args, **kwargs)


class SubType(enum.Enum):
    SJ = 'chs'
    TJ = 'cht'

    def get_name(self):
        if self.name == 'SJ':
            return '简日双语'
        if self.name == 'TJ':
            return '繁日双语'

    def simp_name(self):
        return self.get_name()[:2]

def load_conf():
    global FFMPEG, VSPIPE, X264, ROOT_FOLDER, RING, TEMPLATE, ARGSX264

    if not os.path.exists(CONF):
        # default demo
        conf[KEY_TOOLS] = {
            'ffmpeg': r"D:\Software\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",
            'VSPipe': r"D:\Software\VapourSynth\VapourSynth64Portable\VapourSynth64\VSPipe.exe",
            'x264': r"D:\Software\VapourSynth\VapourSynth64Portable\bin\x264.exe",
            'qaac': r"D:\Software\MeGUI\MeGUI-2913-32\tools\qaac\qaac.exe",
        }
        conf[KEY_PATHS] = {
            'root_folder': r"D:\animes",
            'hint': r'src\ring.mp3',
            'template': r'src\template.vpy'
        }
        conf[KEY_ARGS] = {
            'x264': '--demuxer y4m --preset slower --ref 4 --merange 24 --me umh --bframes 10 --aq-mode 3 --aq-strength 0.7 --deblock 0:0 --trellis 2 --psy-rd 0.6:0.1 --crf 21 --output-depth 8 - -o "{VS_TMP}"'
        }
        conf[KEY_THR] = {
            'task1': '1080chs, 1080cht',
            'task2': '720chs, 720cht',
        }
        with open(CONF, 'w', encoding='utf8') as f:
            conf.write(f)
        raise FileNotFoundError('已生成配置文件 '+CONF+'\n\n请编辑后重新运行本程序！')

    conf.read(CONF, 'utf8')
    try:
        FFMPEG = conf[KEY_TOOLS]['ffmpeg']
        VSPIPE = conf[KEY_TOOLS]['VSPipe']
        X264 = conf[KEY_TOOLS]['x264']

        ARGSX264 = conf[KEY_ARGS]['x264']

        ROOT_FOLDER = conf[KEY_PATHS]['root_folder']
        hint = conf[KEY_PATHS]['hint']
        if not hint:
            print('\n关闭提示音')
        else:
            hint = to_abs(hint)
            if os.path.exists(hint):
                RING = hint.replace('\\', '/')
            else:
                print('\n注意：未找到提示音', hint)
        TEMPLATE = conf[KEY_PATHS]['template']
        TEMPLATE = to_abs(TEMPLATE)
        conf[KEY_PATHS]['template'] = TEMPLATE
        for _, task in conf[KEY_THR].items():
            task = task.split(',')
            task = [j.strip() for j in task]
            TASKS.append(task)
    except KeyError:
        raise AssertionError('配置文件结构不完整，请删除'+CONF+'后重新运行本程序！')

def assert_conf():
    # assert config files
    for sec in [KEY_TOOLS, KEY_PATHS]:
        for name, path in conf[sec].items():
            if name not in SKIP:
                assert os.path.exists(path), '错误！无法找到 [' + sec + '] ' + name + ' 路径 '+path+'，请重新配置conf.ini对应项。'
    args = conf[KEY_ARGS]
    assert '"{VS_TMP}"' in args['x264'], '错误！['+KEY_ARGS+'] 中x264参数格式错误，参数-o的值应为"{VS_TMP}" (含引号)。'
    for task in TASKS:
        for j in task:
            assert j in _TASK_NAMES, '错误！['+KEY_THR+'] 中的任务名无法识别，应为 '+', '.join(_TASK_NAMES)+' 中的一种'
def to_abs(path):
    if os.path.isabs(path): return path
    abs_ = os.path.join(BASE, path)
    if not os.path.exists(abs_):
        abs_ = os.path.join(BASE_TMP, path)
    return abs_

# 获取输入
def parse_workpath():
    if len(sys.argv) < 2:
        raise FileNotFoundError('不支持直接运行！请将待处理文件夹拖放到本程序上！')
    elif not os.path.exists(sys.argv[1]):
        raise FileNotFoundError('待处理文件夹格式错误！输入为'+sys.argv[1])
    workpath = sys.argv[1]
    # folder = os.path.basename(workpath)
    vid = ''
    assS = ''
    assT = ''
    # assert len(os.listdir(workpath)) == 3, '待处理文件夹内容不符合规范，应包含三个文件，一个.mkv/.mp4，两个.ass。'
    for file in os.listdir(workpath):
        full = os.path.join(workpath, file)
        if any([file.endswith(suf) for suf in videosuffs]):
            vid = full
        elif file.endswith('(1).ass'):
            assT = full
        elif file.endswith('.ass'):
            assS = full
    assert vid, '未读取到视频(只支持.mkv/.mp4格式)'
    assert assS, '未读取到简体字幕，命名不能以 (1) 结尾'
    assert assT, '未读取到繁体字幕，命名应以 (1) 结尾'
    return workpath, vid, assS, assT

def get_animefolder_from_input():
    # 读取已存在的番，输入序号，或者新番输入番名
    if DEBUG or DEBUGMODE:
        anime_name = '测试'
    else:
        print('工作目录', ROOT_FOLDER,'\n')
        print('请输入序号或新番全名(用于合集文件夹及成片命名):')
        names = [None]
        i = 1
        for name in os.listdir(ROOT_FOLDER):
            if os.path.isdir(os.path.join(ROOT_FOLDER, name)):
                names.append(name)
                print(f'{i}.', name)
                i += 1
        anime_name = input('>')
        if anime_name.isdigit():
            anime_name = names[int(anime_name)]
    anime_folder = os.path.join(ROOT_FOLDER, anime_name)
    os.makedirs(anime_folder, exist_ok=True)
    return anime_name, anime_folder

# 音频处理
def proc_audio(invid, outaud=M4A_TMP):
    # ffmpeg 提取音频，转码至m4a
    cmdffmpeg = f'"{FFMPEG}" -y -i "{invid}" -vn -c:a aac "{outaud}"'
    print()
    print(cmdffmpeg)
    subprocess.run(cmdffmpeg, check=True, stdout=PIPE, stderr=PIPE)

# 视频处理
def gen_script(template, src, ass, resl):
    assert '{src}' in template and '{ass}' in template and '{w}' in template and '{h}' in template, 'vpy脚本不符合要求！请参考`src/template.vpy`中2～5行设置输入路径和成片分辨率变量！'
    w = '1920' if resl == '1080' else '1280'
    h = '1080' if resl == '1080' else '720'
    return template.format(src=src, ass=ass, w=w, h=h)

def proc_video(invid, inaud, ass, resl, outvid, template, vs_tmp=VS_TMP, prefix=''):
    if not ((DEBUG or SKIPVSTMP) and os.path.exists(vs_tmp)):
        # 生成vpy
        script = gen_script(template, invid, ass, resl)
        with open(SCRIPT_TMP, 'w', encoding='utf8') as f:
            f.write(script)
        # VS压制视频字幕
        cmdvspipe = f'"{VSPIPE}" "{SCRIPT_TMP}" -c y4m -'
        argsx264 = ARGSX264.format(VS_TMP=vs_tmp)
        cmdx264 = X264 + ' ' + argsx264.strip()
        log('VS+x264压制中...', prefix=prefix)
        print()
        print(prefix+'\n'+cmdvspipe,'|',cmdx264)
        vspipe = subprocess.Popen(cmdvspipe, stdout=PIPE, stderr=PIPE)
        x264 = subprocess.run(cmdx264, stdin=vspipe.stdout, check=True, stdout=PIPE, stderr=PIPE)
        vspipe.stdout.close()

    # 与m4a音频封装
    log('封装音频中...', prefix=prefix)
    cmdffmpeg = f'"{FFMPEG}" -y -i "{vs_tmp}" -i "{inaud}" -map 0:v -map 1:a -c:v copy -c:a copy "{outvid}"'
    print()
    print(prefix+'\n'+cmdffmpeg)
    subprocess.run(cmdffmpeg, check=True, stdout=PIPE, stderr=PIPE)

def parse_vidname(vidname):
    res = re.search('E(\d+)', vidname)
    if not res:
        res = re.search('(\d+)', vidname)
    assert res, '解析集数失败！文件名中未找到集数字样！'
    ep = int(res[1])
    return ep

def get_subfoldername(anime_name, ep):
    pref = '[织梦字幕组]'
    res = pref + '[' + anime_name + '][' + '{:02d}'.format(ep) + '集]'
    return res

def get_outvidname(subfoldername, resl, subtype, vi):
    pref = '' if vi <= 1 else f'[V{vi}]'
    mid = '[AVC]'
    res = pref + subfoldername + '[' + resl + 'P]' + mid + '[' + subtype.get_name() + '].mp4'
    if subtype == SubType.TJ:
        res = convlang(res, 'zh-hant')
    return res

def get_avail_outvidname(subfolder, subfoldername, resl, subtype):
    vi = 1
    while True:
        outvidname = get_outvidname(subfoldername, resl, subtype, vi)
        outvid = os.path.join(subfolder, outvidname)
        if not os.path.exists(outvid):
            return outvid
        vi += 1

def sec2hms(secs):
    return '{:0>8}'.format(str(timedelta(seconds=int(secs))))

def playring():
    if os.path.exists(RING):
        playsound(RING)

def parse_jobname(j):
    resl, subname = j[:-3], j[-3:]
    subtype = SubType(subname)
    return resl, subtype

class Job:
    def __init__(self, invid, invidname_noext, aud, ass, resl:str, subtype: SubType, subfolder, subfoldername, template):
        name = f"{resl}{subtype.value}"
        self.invid = invid
        self.aud = aud
        self.ass = ass
        self.resl = resl
        self.subtype = subtype
        self.outvid = get_avail_outvidname(subfolder, subfoldername, resl, subtype)
        self.template = template
        self.vs_tmp = os.path.join(TMP, f'{invidname_noext}_{name}_vs.mp4')
        self.prefix = name + ':'

    def run(self):
        st = time.time()
        self.proc_video()
        log('耗时', sec2hms((time.time() - st)), prefix=self.prefix)

    def proc_video(self):
        log('生成'+self.subtype.simp_name()+self.resl+'p...', prefix=self.prefix)
        proc_video(self.invid, self.aud, self.ass, self.resl, self.outvid, self.template, self.vs_tmp, prefix=self.prefix)
        log('已输出至', self.outvid, prefix=self.prefix)


class TaskRunner(threading.Thread):
    def __init__(self, tasks: list[Job]):
        self.tasks = tasks
        super(TaskRunner, self).__init__()

    def run(self) -> None:
        for task in self.tasks:
            task.run()



def main():
    global workpath, VS_TMP, M4A_TMP
    print(DESCRIPTION)

    load_conf()
    asses = {}  # type: dict[SubType, str]
    workpath, invid, asses[SubType.SJ], asses[SubType.TJ] = parse_workpath()  # full path
    assert_conf()
    if RING: print('\n使用提示音', RING.replace('/', '\\'))
    print('\n使用VS脚本模版', TEMPLATE)
    print('\n使用X264参数', ARGSX264)

    invidname = os.path.basename(invid)
    invidname_noext = os.path.splitext(os.path.basename(invidname))[0]

    ep = parse_vidname(invidname)
    print('\n输入文件夹解析结果：', '\n视频：', os.path.basename(invid), '\n简日字幕：', os.path.basename(asses[SubType.SJ]), '\n繁日字幕：', os.path.basename(asses[SubType.TJ]), '\n集数：', ep)

    anime_name, anime_folder = get_animefolder_from_input()

    subfoldername = get_subfoldername(anime_name, ep)  # 含集数的文件夹
    subfolder = os.path.join(anime_folder, subfoldername)
    os.makedirs(subfolder, exist_ok=True)
    print('\n成片将保存至', subfolder)

    M4A_TMP = os.path.join(TMP, f'{invidname_noext}_m4a.m4a')
    # VS_TMP = os.path.join(TMP, f'{invidname_noext}_vs.mp4')

    aud = M4A_TMP
    if not ((DEBUG or SKIPAUD) and os.path.exists(aud)):
        log('提取音频并转码为m4a...')
        proc_audio(invid, aud)

    with open(TEMPLATE, 'r', encoding='utf8') as f:
        template = f.read()

    task_runners = []
    for task in TASKS:
        jobs = []
        for j in task:
            resl, subtype = parse_jobname(j)
            ass = asses[subtype]
            job = Job(invid, invidname_noext, aud, ass, resl, subtype, subfolder, subfoldername, template)
            jobs.append(job)
        task_runners.append(TaskRunner(jobs))

    st = time.time()
    [task_runner.start() for task_runner in task_runners]
    [task_runner.join() for task_runner in task_runners]
    log('全部结束，共耗时', sec2hms((time.time() - st)))

if __name__ == '__main__':
    try:
        main()
        log('成功！')
        playring()
    except CalledProcessError as err:
        if DEBUG or DEBUGMODE:
            traceback.print_exc()
        else:
            print(err.stderr.decode('utf8'))
            print('\n外部程序执行报错！请检查报错信息，或将问题提交到 https://github.com/zhimengsub/compresser/issues')
    except (FileNotFoundError, AssertionError) as err:
        print()
        print(err)
    except Exception as err:
        traceback.print_exc()
        print('\n发生了未知错误！请将上面的报错信息提交到 https://github.com/zhimengsub/compresser/issues')
    finally:
        if not DEBUG and PURGETMP:
            for name in os.listdir(TMP):
                os.remove(os.path.join(TMP, name))
            os.removedirs(TMP)

        if PAUSE:
            print()
            os.system('pause')