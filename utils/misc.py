import logging
import os.path
import re
import threading
import time
import unittest
from datetime import timedelta
from pycnnum import num2cn
from zhconv import convert as convlang

from utils.conf import Args
from utils.consts import *
from utils.parser import parse_subtaskname
from utils.paths import Paths, TMP

universal_lock = threading.Lock()

def log(*args, prefix='', **kwargs):
    universal_lock.acquire()
    t = '['+time.strftime('%H:%M:%S', time.localtime())+']'
    print()
    if prefix:
        print(t, prefix, *args, **kwargs)
    else:
        print(t, *args, **kwargs)
    universal_lock.release()

def get_avail_outvidname(subfolder, anime_name, ep, resl, subtype, venc, add_prefix_on_exists=True):
    vi = 1
    while True:
        outvidname = _get_outvidname(anime_name, ep, resl, subtype, venc, vi)
        outvid = os.path.join(subfolder, outvidname)
        if add_prefix_on_exists and os.path.exists(outvid):
            vi += 1
            continue
        return outvid, outvidname

def sec2hms(secs):
    return '{:0>8}'.format(str(timedelta(seconds=int(secs))))


# 获取输入
def parse_workpath(workpath):
    if not workpath:
        raise FileNotFoundError('不支持直接运行！请将待处理文件夹拖放到本程序上！')
    elif not os.path.exists(workpath) or not os.path.isdir(workpath):
        raise FileNotFoundError('待处理文件夹不存在！输入为'+workpath)
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
    assert os.path.getsize(vid), '片源大小为0！' + vid
    if any('chs' in subtask for task in Args.TASKS for subtask in task):
        assert assS, '未读取到简体字幕，命名不能以 (1) 结尾'
        assert os.path.getsize(assS), '简体字幕大小为0！' + assS
    if any('cht' in subtask for task in Args.TASKS for subtask in task):
        assert assT, '未读取到繁体字幕，命名应以 (1) 结尾'
        assert os.path.getsize(assT), '繁体字幕大小为0！' + assT
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
    pat = Args.OutPat['folder']
    values = {
        'NAME': anime_name,
        'EP_EN': '{:02d}'.format(ep),
        'EP_ZH': num2cn(ep),
    }
    res = pat.format(**values)
    matches = re.findall(r'\{.+?\}', res)
    assert not matches, '不支持的folder命名规则: ' + ' '.join(matches)

    return res

def _get_bit_depth(vencargs: str):
    res = re.search(r'--output-depth (\d+)', vencargs)
    if res:
        return res[1]
    return 'UNKNOWN'

def _get_outvidname(anime_name, ep, resl, subtype, venc, vi):
    pat = Args.OutPat['file']
    BIT = _get_bit_depth(Args.ARGSX264) if venc.is264() else _get_bit_depth(Args.ARGSX265)
    values = {
        'NAME': anime_name,
        'EP_EN': '{:02d}'.format(ep),
        'EP_ZH': num2cn(ep),
        'VTYPE': venc.get_vtype_name(),
        'BIT': BIT,
        'RESL': resl,
        'LANG': subtype.get_name(),
        'LANG_EN': subtype.get_eng_name(),
        'VER': f'V{vi}'
    }
    if '{VER}' not in pat:
        pat = '[{VER}]' + pat
    res = pat.format(**values)
    res = res.replace('[V1]', '').replace('V1', '')
    res = res.strip()
    if venc.is264():
        res = res + Args.Suffxies.x264_merged_output  # type: str
    elif venc.is265():
        res = res + Args.Suffxies.x265_merged_output
    else:
        raise ValueError('Unknown venc type: ' + str(venc))
    if subtype.is_TJ():
        res = convlang(res, 'zh-hant')
    return res


def get_vs_tmp_path(tmpprefix, venc):
    if venc.is264():
        return os.path.join(TMP, f'{tmpprefix}_vs' + Args.Suffxies.x264_vs_output)
    elif venc.is265():
        return os.path.join(TMP, f'{tmpprefix}_vs' + Args.Suffxies.x265_vs_output)
    else:
        raise ValueError('Unknown venc type: ' + str(venc))

def get_script_tmp_path(tmpprefix):
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
    if not proc.stdout:
        logger.debug('empty!')
    else:
        try:
            logger.debug(proc.stdout.decode('utf8').strip())
        except UnicodeDecodeError:
            try:
                logger.debug(proc.stdout.decode('gbk').strip())
            except UnicodeDecodeError:
                logger.debug('fail to decode!')
    logger.debug('stderr:')
    if not proc.stderr:
        logger.debug('empty!')
    else:
        try:
            logger.debug(proc.stderr.decode('utf8').strip())
        except UnicodeDecodeError:
            try:
                logger.debug(proc.stderr.decode('gbk').strip())
            except UnicodeDecodeError:
                logger.debug('fail to decode!')



class SubTaskHelper:
    """拆分subtask字符串，便于organize_tasks处理二压情况"""
    def __init__(self, subtask_str):
        resl, subtype, venc, noass = parse_subtaskname(subtask_str)
        self.resl = resl
        self.subtype = subtype
        self.venc = venc
        self.noass = noass
        self.logprefix = f'{resl}{subtype.value}{venc.value}:'

    def str_format(self, *, venc: bool = True, noass: bool = True):
        s = self.resl + self.subtype.value
        if venc:
            s += self.venc.value
        if noass:
            s += '_noass'
        return s

    def str_wo_venc(self):
        s = self.resl + self.subtype.value
        if self.noass:
            s += '_noass'
        return s

    def str_full(self):
        s = self.resl + self.subtype.value + self.venc.value
        if self.noass:
            s += '_noass'
        return s

    def __eq__(self, other):
        return self.str_full() == other.str_full()

    def __str__(self):
        return self.str_full()

def organize_tasks(tasks: list[list[str]], NO_ASS_SJ: bool, NO_ASS_TJ: bool) -> (list[list[str]], dict[SubTaskHelper]):
    '''tests:
    [ ['1080chs265', '1080cht265'],['720chs264','720cht264'] ], True, True -> [[ ['1080chs265', '1080cht265', '720chs264_noass','720cht264_noass'] ] , {}]
    [ ['1080chs265', '720cht264'],['1080cht265','720chs264'] ], True, True -> [[ ['1080chs265', '720chs264_noass', '1080cht265','720cht264_noass'] ], {}]
    [ ['1080chs265'] , ['1080cht265'], ['720chs264'], ['720cht264'] ], True, True -> [[ ['1080chs265', '720chs264_noass'], ['1080cht265','720cht264_noass'] ], {}]
    [ ['1080chs265'], ['720cht264'] ], True, True -> [[ ['1080chs265'] ], {'720cht_noass': '720cht264_noass'}]
    :param NO_ASS_SJ: 不需要ass文件（需要二压）
    :returns: [out_tasks, isolated_noass_subtasks: 没有对应1080版的720二压任务]
    '''
    subtaskobjs_noass: dict[SubTaskHelper] = {}  # 需要二压的任务
    tasks_1080: list[list[str]] = []
    # 取出720版，如果有对应的1080版则插入其后方
    # filter out 720 subtasks if NO ASS
    for task in tasks:
        task_1080 = []
        for subtask in task:
            s_obj = SubTaskHelper(subtask)
            if s_obj.resl == '720' and (s_obj.subtype.is_SJ and NO_ASS_SJ or s_obj.subtype.is_TJ() and NO_ASS_TJ):
                s_obj = SubTaskHelper(subtask + '_noass')
                subtaskobjs_noass[s_obj.str_wo_venc()] = s_obj
            else:
                task_1080.append(subtask)
        if task_1080:
            tasks_1080.append(task_1080)
    # insert 720 subtasks back after corresponding 1080/normal subtask
    out_tasks = []
    for task_1080 in tasks_1080:
        out_task = task_1080.copy()
        for subtask_1080 in task_1080:
            resl_1080, subtype_1080, _, _ = parse_subtaskname(subtask_1080)
            if resl_1080 == '1080':
                subtask_noass = '720' + subtype_1080.value + '_noass'
                try:
                    s_obj = subtaskobjs_noass.pop(subtask_noass)
                    out_task.append(s_obj.str_full())
                except KeyError:
                    pass
        if out_task:
            out_tasks.append(out_task)
    # 没有对应1080版的720二压任务作为单独的tasks加入，后续再判断是否需要abort
    if subtaskobjs_noass:
        out_tasks.append([s_obj_noass.str_full() for s_obj_noass in subtaskobjs_noass.values()])

    return out_tasks, subtaskobjs_noass


class Test(unittest.TestCase):
    def test_organize_tasks(self):
        self.assertEqual(organize_tasks([ ['1080chs265', '1080cht265'],['720chs264','720cht264'] ], True, True),
                         ([ ['1080chs265', '1080cht265', '720chs264_noass','720cht264_noass'] ] , {}))

        self.assertEqual(organize_tasks([ ['1080chs265', '720cht264'],['1080cht265','720chs264'] ], True, True),
                         ([ ['1080chs265', '720chs264_noass'], ['1080cht265','720cht264_noass'] ], {}))

        self.assertEqual(organize_tasks([ ['1080chs265'] , ['1080cht265'], ['720chs264'], ['720cht264'] ], True, True),
                         ([ ['1080chs265', '720chs264_noass'], ['1080cht265','720cht264_noass'] ], {}))

        self.assertEqual(organize_tasks([ ['1080chs265'], ['720cht264'] ], True, True),
                         ([ ['1080chs265'], ['720cht264_noass'] ], {'720cht_noass': SubTaskHelper('720cht264_noass')}))

        self.assertEqual(organize_tasks([ ['1080chs264', '1080cht264'],['720chs264','720cht264'] ], True, True),
                         ([ ['1080chs264', '1080cht264', '720chs264_noass','720cht264_noass'] ] , {}))

        self.assertEqual(organize_tasks([ ['1080chs264', '720cht264'],['1080cht264','720chs264'] ], True, True),
                         ([ ['1080chs264', '720chs264_noass'], ['1080cht264','720cht264_noass'] ], {}))

        self.assertEqual(organize_tasks([ ['1080chs264'] , ['1080cht264'], ['720chs264'], ['720cht264'] ], True, True),
                         ([ ['1080chs264', '720chs264_noass'], ['1080cht264','720cht264_noass'] ], {}))

        self.assertEqual(organize_tasks([ ['1080chs264'], ['720cht264'] ], True, True),
                         ([ ['1080chs264'], ['720cht264_noass'] ], {'720cht_noass': SubTaskHelper('720cht264_noass')}))
