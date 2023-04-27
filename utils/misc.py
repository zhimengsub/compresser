import logging
import os.path
import re
import time
from datetime import timedelta

from zhconv import convert as convlang

from utils.conf import Args
from utils.consts import *
from utils.paths import Paths, TMP
from utils.subtype import SubType


def log(*args, prefix='', **kwargs):
    t = '['+time.strftime('%H:%M:%S', time.localtime())+']'
    print()
    if prefix:
        print(t, prefix, *args, **kwargs)
    else:
        print(t, *args, **kwargs)

def parse_jobname(j: str) -> tuple[str, SubType, bool]:
    noass = '_noass' in j
    if noass:
        resl, subname = j[:-9], j[-9:]
    else:
        resl, subname = j[:-3], j[-3:]
    subtype = SubType(subname)
    return resl, subtype, noass

def get_avail_outvidname(subfolder, subfoldername, resl, subtype, add_prefix_on_exists=True):
    vi = 1
    while True:
        outvidname = get_outvidname(subfoldername, resl, subtype, vi)
        outvid = os.path.join(subfolder, outvidname)
        if add_prefix_on_exists and os.path.exists(outvid):
            vi += 1
            continue
        return outvid

def sec2hms(secs):
    return '{:0>8}'.format(str(timedelta(seconds=int(secs))))


# 获取输入
def parse_workpath():
    if len(sys.argv) < 2:
        raise FileNotFoundError('不支持直接运行！请将待处理文件夹拖放到本程序上！')
    elif not os.path.exists(sys.argv[1]) or not os.path.isdir(sys.argv[1]):
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
    assert vid, '未读取到视频(只支持 ' + '/'.join(videosuffs) + ' 格式)'
    if any('chs' in task for task in Args.TASKS):
        assert assS, '未读取到简体字幕，命名不能以 (1) 结尾'
    if any('cht' in task for task in Args.TASKS):
        assert assT, '未读取到繁体字幕，命名应以 (1) 结尾'
    return workpath, vid, assS, assT

def prompt_for_animefolder():
    # 读取已存在的番，输入序号，或者新番输入番名
    if USETESTFOLDER:
        anime_name = '测试'
    else:
        print('\n请输入序号或新番全名(用于合集文件夹及成片命名):')
        names = [None]
        i = 1
        for name in os.listdir(Paths.ROOT_FOLDER):
            if os.path.isdir(os.path.join(Paths.ROOT_FOLDER, name)):
                names.append(name)
                print(f'{i}.', name)
                i += 1
        anime_name = input('>')
        if anime_name.isdigit():
            anime_name = names[int(anime_name)]
    anime_folder = os.path.join(Paths.ROOT_FOLDER, anime_name)
    os.makedirs(anime_folder, exist_ok=True)
    return anime_name, anime_folder


def parse_vidname(vidname):
    res = re.search('E(\d+)', vidname)
    if not res:
        res = re.search('(\d+)', vidname)
    assert res, '解析集数失败！文件名中未找到集数字样！'
    ep = int(res[1])
    return ep

def get_subfoldername(anime_name, ep):
    pref = Args.OutPat['prefix']
    res = pref + '[' + anime_name + '][' + '{:02d}'.format(ep) + '集]'
    return res

def get_outvidname(subfoldername, resl, subtype, vi):
    pref = '' if vi <= 1 else f'[V{vi}]'
    mid = '[AVC]'
    res = pref + subfoldername + '[' + resl + 'P]' + mid + '[' + subtype.get_name() + ']' + Args.Suffxies.merged_output
    if subtype.is_TJ():
        res = convlang(res, 'zh-hant')
    return res


def get_vs_tmp(tmpprefix):
    return os.path.join(TMP, f'{tmpprefix}_vs' + Args.Suffxies.x264_output)

def get_script_tmp(tmpprefix):
    return os.path.join(TMP, f'{tmpprefix}_script.vpy')

def log_pipe(logger: logging.Logger, cmd, pipe):
    logger.debug('\n' + cmd)
    logger.debug('stdout:')
    with pipe.stdout:
        for line in iter(pipe.stdout.readline, b''):
            logger.debug(line.decode('utf8').strip())
    logger.debug('stderr:')
    with pipe.stderr:
        for line in iter(pipe.stderr.readline, b''):
            logger.debug(line.decode('utf8').strip())


def log_process(logger, cmd, proc):
    logger.debug('\n' + cmd)
    logger.debug('stdout:')
    logger.debug(proc.stdout.decode('utf8').strip())
    logger.debug('stderr:')
    logger.debug(proc.stderr.decode('utf8').strip())

# 是否需要二压
def has_img(ass) -> bool:
    if not ass:
        return False
    with open(ass, 'r', encoding='utf_8_sig') as f:
        while l:= f.readline():
            if re.search(r'\\\dimg', l):
                return True
    return False

def organize_tasks(tasks: list[list[str]], NO_ASS_SJ: bool, NO_ASS_TJ: bool) -> (list[list[str]], list[str]):
    '''tests:
    [ ['1080chs', '1080cht'],['720chs','720cht'] ] -> [ ['1080chs', '1080cht', '720chs_noass','720cht_noass'] ]
    [ ['1080chs', '720cht'],['1080cht','720chs'] ] -> [ ['1080chs', '720chs_noass', '1080cht','720cht_noass'] ]
    [ ['1080chs'] , ['1080cht'], ['720chs'], ['720cht'] ] -> [ ['1080chs', '720chs_noass'], ['1080cht','720cht_noass'] ]
    :param NO_ASS_SJ: 不需要ass文件（需要二压）
    :returns: [out_tasks, isolated_noass_jobs: 没有对应1080版的720二压任务]
    '''
    noass_jobs = []  # 需要二压的任务
    tasks_normal = []
    # 取出720版，如果有对应的1080版则插入其后方
    # filter out 720 jobs if NO ASS
    for task in tasks:
        task_normal = []
        for j in task:
            if j.startswith('720') and (j.endswith('chs') and NO_ASS_SJ or j.endswith('cht') and NO_ASS_TJ):
                noass_jobs.append(j + '_noass')
            else:
                task_normal.append(j)
        if task_normal:
            tasks_normal.append(task_normal)
    # insert 720 jobs back after corresponding 1080/normal job
    out_tasks = []
    for task_normal in tasks_normal:
        out_task = task_normal.copy()
        for j_normal in task_normal:
            if j_normal.startswith('1080'):
                j_720_noass = j_normal.replace('1080', '720') + '_noass'
                if j_720_noass in noass_jobs:
                    out_task.append(j_720_noass)
                    noass_jobs.remove(j_720_noass)
        if out_task:
            out_tasks.append(out_task)
    # 没有对应1080版的720二压任务作为单独的tasks加入，后续再判断是否需要abort
    if noass_jobs:
        out_tasks.append([j_720_noass for j_720_noass in noass_jobs])

    return out_tasks, noass_jobs
