import os
import shutil
import subprocess
import threading
import time
import traceback
from logging import Logger
from pathlib import Path
from string import Template
from subprocess import CalledProcessError, PIPE

from playsound import playsound, PlaysoundException

from utils.conf import Args, load_conf
import utils.consts
from utils.consts import *
from utils.fonts import FontChecker
from utils.logger import initFileLogger
from utils.misc import log, prompt_for_animefolder, get_subfoldername, sec2hms, \
    log_process, organize_tasks, get_vs_tmp_path, get_script_tmp_path, SubTaskHelper, get_avail_outvidname, \
    parse_workpath, parse_vidname, _get_bit_depth
from utils.assfile import has_img, check_font_avail
from utils.paths import TMP, Paths
from utils.subtype import SubType
from utils.sysargs import get_sysargs
from utils.vencodertype import VEncType

VER = 'v2.1.4'
DESCRIPTION = '************************************************************************************\n' + \
              '* 织梦字幕组自动压制工具\n' + \
              '* —— ' + VER + ' by 谢耳朵w\n*\n' + \
              '* 使用说明、获取最新版本、提交建议和错误请前往 https://github.com/zhimengsub/compresser\n' + \
              '************************************************************************************'


# 音频处理
def proc_audio(invid, outaud, logger_file, debug=False):
    # 直接用ffmpeg提取音频
    cmdffmpeg = f'"{Paths.FFMPEG}" -y -i "{invid}" -c:a copy -vn "{outaud}"'
    log('提取音频:\n', cmdffmpeg)
    logger_file.debug(cmdffmpeg)
    ffmpeg = None
    try:
        if debug:
            ffmpeg = subprocess.run(cmdffmpeg, check=True)
        else:
            ffmpeg = subprocess.run(cmdffmpeg, check=True, stdout=PIPE, stderr=PIPE)
    finally:
        if logger_file and ffmpeg and not debug:
            logger_file.debug('')
            log_process(logger_file, cmdffmpeg, ffmpeg)

# 视频处理
def gen_script(template, src, ass, resl):
    assert '$src' in template and ('$ass' in template if ass else True) and '$w' in template and '$h' in template, 'vpy脚本不符合要求！请参考`src/template.vpy`中2～5行设置输入路径和成片分辨率变量！'
    w = '1920' if resl == '1080' else '1280'
    h = '1080' if resl == '1080' else '720'
    return Template(template).substitute(src=src, ass=ass, w=w, h=h)

def proc_video(invid, inaud, resl, venc, outvid, template, vs_tmp, script_tmp, prefix='', logger_file:Logger=None, ass=None, debug=False):
    if not (SKIPVSTMP and os.path.exists(vs_tmp)):
        if venc.is264():
            # 生成vpy
            script = gen_script(template, invid, ass, resl)
            with open(script_tmp, 'w', encoding='utf8') as f:
                f.write(script)
            # VS压制视频字幕
            cmdvspipe = f'"{Paths.VSPIPE}" "{script_tmp}" -c y4m -'
            argsx264 = Args.ARGSX264.format(VS_TMP=vs_tmp)
            cmdx264 = f'"{Paths.X264}" {argsx264.strip()}'
            log('VS+x264压制:\n', cmdvspipe,'|',cmdx264, prefix=prefix)
            logger_file.debug(cmdvspipe)
            vspipe = subprocess.Popen(cmdvspipe, stdout=PIPE, stderr=PIPE)
            x264 = None
            try:
                if debug:
                    x264 = subprocess.run(cmdx264, stdin=vspipe.stdout)
                else:
                    x264 = subprocess.run(cmdx264, stdin=vspipe.stdout, stdout=PIPE, stderr=PIPE)
            finally:
                if logger_file and x264 and not debug:
                    logger_file.debug('')
                    log_process(logger_file, cmdx264, x264)
            vspipe.stdout.close()
            vspipe.stderr.close()
        elif venc.is265():
            # 生成vpy
            script = gen_script(template, invid, ass, resl)
            with open(script_tmp, 'w', encoding='utf8') as f:
                f.write(script)
            # VS压制视频字幕
            cmdvspipe = f'"{Paths.VSPIPE}" "{script_tmp}" -c y4m -'
            argsx265 = Args.ARGSX265.format(VS_TMP=vs_tmp)
            cmdx265 = f'"{Paths.X265}" {argsx265.strip()}'
            log('VS+x265压制:\n', cmdvspipe,'|',cmdx265, prefix=prefix)
            logger_file.debug(cmdvspipe)
            vspipe = subprocess.Popen(cmdvspipe, stdout=PIPE, stderr=PIPE)
            x265 = None
            try:
                if debug:
                    x265 = subprocess.run(cmdx265, stdin=vspipe.stdout)
                else:
                    x265 = subprocess.run(cmdx265, stdin=vspipe.stdout, stdout=PIPE, stderr=PIPE)
            finally:
                if logger_file and x265 and not debug:
                    logger_file.debug('')
                    log_process(logger_file, cmdx265, x265)
            vspipe.stdout.close()
            vspipe.stderr.close()
        else:
            raise NotImplementedError('Unknown venc: ' + venc.value)

    # 检查视频压制情况
    assert os.path.exists(vs_tmp) and os.path.getsize(vs_tmp) != 0, '压制视频失败！无法获取' + str(vs_tmp)

    # 与m4a音频封装
    cmdmp4box = f'"{Paths.MP4BOX}" -add "{vs_tmp}#trackID=1:par=1:1:name=" -add "{inaud}:name=" -new "{outvid}"'
    log('封装音频:\n', cmdmp4box, prefix=prefix)
    mp4box = None
    try:
        if debug:
            mp4box = subprocess.run(cmdmp4box, check=True)
        else:
            mp4box = subprocess.run(cmdmp4box, check=True, stdout=PIPE, stderr=PIPE)
    finally:
        if logger_file and mp4box and not debug:
            logger_file.debug('')
            log_process(logger_file, cmdmp4box, mp4box)
    assert os.path.exists(outvid) and os.path.getsize(outvid) != 0, '封装音频失败！无法获取' + str(outvid)

def playring():
    if os.path.exists(Paths.RING):
        playsound(Paths.RING)

def remove_tmps(tmp_fullpaths: list[str]):
    for tmp in tmp_fullpaths:
        if os.path.exists(tmp):
            os.remove(tmp)


def main(sysargs, tmp_fullpaths):
    global workpath, AUD_TMP
    ass_paths = {}  # type: dict[SubType, str]
    workpath, invid, ass_paths[SubType.SJ], ass_paths[SubType.TJ] = parse_workpath(sysargs.work_path)  # full path
    if Paths.RING: print('\n使用提示音：', Paths.RING.replace('/', '\\'))
    if Args.ARGSX264:
        print('\n使用X264参数：', Args.ARGSX264)
    if Args.ARGSX265:
        print('\n使用X265参数：', Args.ARGSX265)

    print('\n工作目录：', Paths.ROOT_FOLDER)

    print('\n成片文件夹命名格式：', Args.OutPat['folder'])
    print('\n成片文件命名格式：', Args.OutPat['file'])

    # 是否不填加字幕（需要二压）
    NO_ASS_SJ = has_img(ass_paths[SubType.SJ])
    NO_ASS_TJ = has_img(ass_paths[SubType.TJ])
    isolated_noass_subtaskobjs = {}
    if NO_ASS_SJ or NO_ASS_TJ:
        Args.TASKS, isolated_noass_subtaskobjs = organize_tasks(Args.TASKS, NO_ASS_SJ, NO_ASS_TJ)
        print('\n压制任务：（需要二压，已调整压制任务顺序！）')
    else:
        print('\n压制任务：')

    for i, task in enumerate(Args.TASKS):
        print(f'{i + 1}. ' + ' '.join(task))

    print('\n使用VS脚本模版：\n' + '\n'.join(f'{j}：{Paths.TemplatePaths[j]}' for task in Args.TASKS for j in task))

    invidname = os.path.basename(invid)
    invidname_noext = os.path.splitext(os.path.basename(invidname))[0]

    ep = parse_vidname(invidname)
    print('\n输入文件夹解析结果：', '\n视频：', os.path.basename(invid), '\n简日字幕：', os.path.basename(ass_paths[SubType.SJ]) or '无', '\n繁日字幕：', os.path.basename(ass_paths[SubType.TJ]) or '无', '\n集数：', ep)

    font_checker = FontChecker()
    failed_fontnames = check_font_avail(ass_paths[SubType.SJ], font_checker)
    failed_fontnames2 = check_font_avail(ass_paths[SubType.TJ], font_checker)
    failed_fontnames = set(failed_fontnames).union(set(failed_fontnames2))
    if failed_fontnames:
        print('\n字体检查结果：\n以下字体*可能*未安装（可能误报）：')
        print('\n'.join(failed_fontnames))
    else:
        print('\n字体检查结果：通过')

    if Args.ARGSX264 and _get_bit_depth(Args.ARGSX264) == 'UNKNOWN':
        print('\n注意：x264参数缺少--output-depth，成片命名可能出错，请自行检查结果！')
    if Args.ARGSX265 and _get_bit_depth(Args.ARGSX265) == 'UNKNOWN':
        print('\n注意：x265参数缺少--output-depth，成片命名可能出错，请自行检查结果！')

    anime_name, anime_folder = prompt_for_animefolder()

    subfoldername = get_subfoldername(anime_name, ep)  # 含集数的文件夹
    subfolder = os.path.join(anime_folder, subfoldername)
    os.makedirs(subfolder, exist_ok=True)
    print('\n成片将保存至')
    print(subfolder)

    AUD_TMP = os.path.join(TMP, f'{invidname_noext}_audio.mp4')

    task_runners: list[Task] = []
    prev_1080subtaskobjs: list[SubTaskHelper] = []  # 用于判断二压片子的1080版任务名
    for task in Args.TASKS:
        subtasks: list[Subtask] = []
        for s in task:
            s_obj = SubTaskHelper(s)
            resl, subtype, venc, noass = s_obj.resl, s_obj.subtype, s_obj.venc, s_obj.noass
            if resl == '1080':
                prev_1080subtaskobjs.append(s_obj)
            if noass:
                # 需要二压
                # 720的输入应该改成1080的输出
                outvid_1080_264, _ = get_avail_outvidname(subfolder, anime_name, ep, '1080', subtype, VEncType('264'), add_prefix_on_exists=False)
                outvid_1080_265, _ = get_avail_outvidname(subfolder, anime_name, ep, '1080', subtype, VEncType('265'), add_prefix_on_exists=False)
                # 检查是否存在对应的1080任务，或存在对应的1080成片
                if (
                    #不存在对应的1080任务
                    s in [s_obj.str_full() for s_obj in isolated_noass_subtaskobjs.values()] and
                    #不存在1080成片
                    not os.path.exists(outvid_1080_264) and
                    not os.path.exists(outvid_1080_265)
                ):
                    raise AssertionError('错误！需要二压，但[' + s + ']任务不存在1080版任务或成片！')

                # 先找成片，优先选与1080编码一致的成片
                if os.path.exists(outvid_1080_265) or os.path.exists(outvid_1080_264):
                    if s_obj.venc.is264():
                        outvid_1080 = outvid_1080_264 if os.path.exists(outvid_1080_264) else outvid_1080_265
                    elif s_obj.venc.is265():
                        outvid_1080 = outvid_1080_265 if os.path.exists(outvid_1080_265) else outvid_1080_264
                    else:
                        raise NotImplementedError()
                    log('需要二压，复用1080P成片：', outvid_1080, prefix=s_obj.logprefix)
                else:
                    # 不存在成片，说明成片来自1080版任务，获取1080版的片名
                    outvid_1080 = None
                    for prev_1080subtaskobj in prev_1080subtaskobjs:
                        if prev_1080subtaskobj.str_wo_venc().replace('1080', '720') == s_obj.str_format(venc=False, noass=False):
                            venc_1080 = prev_1080subtaskobj.venc
                            outvid_1080, _ = get_avail_outvidname(subfolder, anime_name, ep, '1080', subtype, venc_1080, add_prefix_on_exists=False)
                            log('需要二压，待1080P任务', prev_1080subtaskobj.str_full(), '完成后复用。', prefix=s_obj.logprefix)
                    if outvid_1080 is None:
                        raise NotImplementedError()
                subtask = Subtask(s, invidname_noext, outvid_1080, AUD_TMP, subfolder, anime_name, ep, asssrc_path=None, debug=sysargs.debug)
            else:
                asssrc_path = ass_paths[subtype]
                subtask = Subtask(s, invidname_noext, invid, AUD_TMP, subfolder, anime_name, ep, asssrc_path, debug=sysargs.debug)
            log('成片名：', subtask.outvidname, prefix=s_obj.logprefix)
            tmp_fullpaths.extend(subtask.tmp_fullpaths)
            subtasks.append(subtask)
        task_runners.append(Task(subtasks))

    if not (SKIPAUD and os.path.exists(AUD_TMP)):
        logger_file = initFileLogger('audio')
        proc_audio(invid, AUD_TMP, logger_file, debug=sysargs.debug)
        tmp_fullpaths.extend([AUD_TMP])

    [task_runner.start() for task_runner in task_runners]
    [task_runner.join() for task_runner in task_runners]

    return tmp_fullpaths

class Subtask:
    def __init__(self, subtask_str, invidname_noext, invid, aud, subfolder, anime_name, ep, asssrc_path=None, debug=False):
        s_obj = SubTaskHelper(subtask_str)
        resl, subtype, venc, noass = s_obj.resl, s_obj.subtype, s_obj.venc, s_obj.noass
        subtaskname = s_obj.str_full()  # 1080chs265
        self.name = subtaskname
        self.logprefix = s_obj.logprefix
        prefix_tmp = f'{invidname_noext}_{subtaskname}'

        self.invid = invid
        self.aud = aud

        self.asstmp_path = ''
        if not noass:
            asstmp_path = os.path.join(TMP, f'{prefix_tmp}_ass.ass')
            if not os.path.exists(asstmp_path):
                shutil.copyfile(asssrc_path, asstmp_path)
            self.asstmp_path = asstmp_path

        self.resl = resl
        self.subtype = subtype
        self.venc = venc
        self.outvid, self.outvidname = get_avail_outvidname(subfolder, anime_name, ep, resl, subtype, venc, add_prefix_on_exists=True)
        self.vs_tmp_path = get_vs_tmp_path(prefix_tmp, venc)
        self.script_tmp_path = get_script_tmp_path(prefix_tmp)
        with open(Paths.TemplatePaths[subtaskname], 'r', encoding='utf8') as f:
            self.template = f.read()
        self.logger_file = initFileLogger(subtaskname)
        self.debug = debug

    @property
    def tmp_fullpaths(self):
        return [self.asstmp_path, self.vs_tmp_path, self.script_tmp_path]

    def run(self):
        st = time.time()
        log('生成' + self.subtype.simp_name() + self.resl + 'p...', prefix=self.logprefix)
        try:
            assert os.path.getsize(self.invid) > 0, '片源大小为0！' + str(self.invid)
            proc_video(
                self.invid,
                self.aud,
                self.resl,
                self.venc,
                self.outvid,
                self.template,
                self.vs_tmp_path,
                self.script_tmp_path,
                prefix=self.logprefix,
                logger_file=self.logger_file,
                ass=self.asstmp_path,
                debug=self.debug
            )
        except Exception as e:
            log('错误！' + str(e), prefix=self.logprefix)
            raise e
        else:
            log('已输出至', self.outvid, prefix=self.logprefix)
        finally:
            log('耗时', sec2hms((time.time() - st)), prefix=self.logprefix)

    def __str__(self):
        return self.name

class Task(threading.Thread):
    def __init__(self, subtasks: list[Subtask]):
        self.subtasks = subtasks
        self._exceptions = {}
        super(Task, self).__init__()

    def run(self) -> None:
        for subtask in self.subtasks:
            try:
                subtask.run()
            except Exception as e:
                self._exceptions[subtask] = e

    def join(self, *args, **kwargs):
        super(Task, self).join(*args, **kwargs)
        if self._exceptions:
            for subtask, e in self._exceptions.items():
                raise e


if __name__ == '__main__':
    tmp_fullpaths = []  # record tmp files for removal

    print(DESCRIPTION)
    sysargs = get_sysargs()

    print('\n配置解析结果：')
    conf_path = str(Path(sysargs.conf_path).absolute())
    print('\n配置文件路径：', conf_path)
    load_conf(conf_path)

    st = time.time()
    try:
        main(sysargs, tmp_fullpaths)
    except CalledProcessError as err:
        if DEBUGMODE:
            traceback.print_exc()
        elif sysargs.debug:
            traceback.print_exc()
            print('\n外部程序执行报错！请检查报错信息，或将问题提交到 https://github.com/zhimengsub/compresser/issues')
        else:
            print(err.stderr.decode('utf8'))
            print('\n外部程序执行报错！请检查报错信息，或将问题提交到 https://github.com/zhimengsub/compresser/issues')
    except (FileNotFoundError, AssertionError, PlaysoundException) as err:
        print()
        print(err)
        print('\n发生了校验错误！请将上面的报错信息提交到 https://github.com/zhimengsub/compresser/issues')
    except Exception as err:
        traceback.print_exc()
        print('\n发生了未知错误！请将上面的报错信息提交到 https://github.com/zhimengsub/compresser/issues')
    else:
        log('成功！')
        playring()
    finally:
        log('全部结束，共耗时', sec2hms((time.time() - st)))
        if utils.consts.PURGETMP:
            remove_tmps(tmp_fullpaths)

        if PAUSE:
            print()
            os.system('pause')