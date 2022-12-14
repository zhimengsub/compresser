import logging
import os.path
import re
import time
from datetime import timedelta

from zhconv import convert as convlang

from utils.conf import Args
from utils.consts import *
from utils.paths import Paths
from utils.subtype import SubType


def log(*args, prefix='', **kwargs):
    t = '['+time.strftime('%H:%M:%S', time.localtime())+']'
    print()
    if prefix:
        print(t, prefix, *args, **kwargs)
    else:
        print(t, *args, **kwargs)

def parse_jobname(j) -> tuple[str, SubType]:
    resl, subname = j[:-3], j[-3:]
    subtype = SubType(subname)
    return resl, subtype

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
    assert vid, '未读取到视频(只支持.mkv/.mp4格式)'
    if any('chs' in task for task in Args.TASKS):
        assert assS, '未读取到简体字幕，命名不能以 (1) 结尾'
    if any('cht' in task for task in Args.TASKS):
        assert assT, '未读取到繁体字幕，命名应以 (1) 结尾'
    return workpath, vid, assS, assT

def get_animefolder_from_input():
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
    pref = '[织梦字幕组]'
    res = pref + '[' + anime_name + '][' + '{:02d}'.format(ep) + '集]'
    return res

def get_outvidname(subfoldername, resl, subtype, vi):
    pref = '' if vi <= 1 else f'[V{vi}]'
    mid = '[AVC]'
    res = pref + subfoldername + '[' + resl + 'P]' + mid + '[' + subtype.get_name() + ']' + Args.Suffxies.merged_output
    if subtype == SubType.TJ:
        res = convlang(res, 'zh-hant')
    return res


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
