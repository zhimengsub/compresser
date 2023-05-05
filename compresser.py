import os
import shutil
import subprocess
import threading
import time
import traceback
from logging import Logger
from pathlib import Path
from subprocess import CalledProcessError, PIPE

from playsound import playsound, PlaysoundException

from utils.conf import Args, load_conf
from utils.consts import *
from utils.logger import initFileLogger
from utils.misc import log, parse_workpath, parse_vidname, prompt_for_animefolder, get_subfoldername, sec2hms, \
    parse_subtaskname, log_process, has_img, organize_tasks, get_avail_outvidname, get_vs_tmp_path, get_script_tmp_path
from utils.paths import TMP, Paths
from utils.subtype import SubType
from utils.sysargs import get_sysargs

VER = 'v2.0.10.001'
DESCRIPTION = '************************************************************************************\n' + \
              '* 织梦字幕组自动压制工具\n' + \
              '* —— ' + VER + ' by 谢耳朵w\n*\n' + \
              '* 使用说明、获取最新版本、提交建议和错误请前往 https://github.com/zhimengsub/compresser\n' + \
              '************************************************************************************'


# 音频处理
def proc_audio(invid, outaud, template, script_tmp, logger_file):
    # 生成y音频用vpy
    script = gen_audio_script(template, invid)
    with open(script_tmp, 'w', encoding='utf8') as f:
        f.write(script)
    # vs打开后喂给qaac
    cmdvspipe = f'"{Paths.VSPIPE}" "{script_tmp}" -o 1 -c wav -'
    argsqaac = Args.ARGSQAAC.format(M4A_TMP=outaud)
    assert argsqaac
    cmdqaac = f'"{Paths.QAAC}" {argsqaac.strip()}'
    log(cmdvspipe, '|', cmdqaac)
    logger_file.debug(cmdvspipe)
    vspipe = subprocess.Popen(cmdvspipe, stdout=PIPE, stderr=PIPE)
    qaac = None
    try:
        qaac = subprocess.run(cmdqaac, stdin=vspipe.stdout, stdout=PIPE, stderr=PIPE)
    finally:
        if logger_file and qaac:
            logger_file.debug('')
            log_process(logger_file, cmdqaac, qaac)
    vspipe.stdout.close()
    vspipe.stderr.close()

def gen_audio_script(template, src):
    assert '{src}' in template, 'vpy脚本不符合要求！需要设置输入路径变量为r"{src}"！'
    return template.format(src=src)

# 视频处理
def gen_script(template, src, ass, resl):
    assert '{src}' in template and ('{ass}' in template if ass else True) and '{w}' in template and '{h}' in template, 'vpy脚本不符合要求！请参考`src/template.vpy`中2～5行设置输入路径和成片分辨率变量！'
    w = '1920' if resl == '1080' else '1280'
    h = '1080' if resl == '1080' else '720'
    return template.format(src=src, ass=ass, w=w, h=h)

def proc_video(invid, inaud, resl, outvid, template, vs_tmp, script_tmp, prefix='', logger_file:Logger=None, ass=None):
    if not (SKIPVSTMP and os.path.exists(vs_tmp)):
        # 生成vpy
        script = gen_script(template, invid, ass, resl)
        with open(script_tmp, 'w', encoding='utf8') as f:
            f.write(script)
        # VS压制视频字幕
        cmdvspipe = f'"{Paths.VSPIPE}" "{script_tmp}" -c y4m -'
        argsx264 = Args.ARGSX264.format(VS_TMP=vs_tmp)
        assert argsx264
        cmdx264 = f'"{Paths.X264}" {argsx264.strip()}'
        log('VS+x264压制中...', prefix=prefix)
        log(cmdvspipe,'|',cmdx264, prefix=prefix)
        logger_file.debug(cmdvspipe)
        vspipe = subprocess.Popen(cmdvspipe, stdout=PIPE, stderr=PIPE)
        x264 = None
        try:
            x264 = subprocess.run(cmdx264, stdin=vspipe.stdout, stdout=PIPE, stderr=PIPE)
        finally:
            if logger_file and x264:
                logger_file.debug('')
                log_process(logger_file, cmdx264, x264)
        vspipe.stdout.close()
        vspipe.stderr.close()

    # 与m4a音频封装
    log('封装音频中...', prefix=prefix)
    cmdffmpeg = f'"{Paths.FFMPEG}" -y -i "{vs_tmp}" -i "{inaud}" -c:v copy -c:a copy -map 0:v:0 -map 1:a:0 "{outvid}"'
    log(cmdffmpeg, prefix=prefix)
    ffmpeg = None
    try:
        ffmpeg = subprocess.run(cmdffmpeg, check=True, stdout=PIPE, stderr=PIPE)
    finally:
        if logger_file and ffmpeg:
            logger_file.debug('')
            log_process(logger_file, cmdffmpeg, ffmpeg)

def playring():
    if os.path.exists(Paths.RING):
        playsound(Paths.RING)

def main():
    global workpath, M4A_TMP
    print(DESCRIPTION)
    sysargs = get_sysargs()

    conf_path = Path(sysargs.conf_path).absolute()
    print('\n配置文件路径：', conf_path)

    load_conf(conf_path)

    ass_paths = {}  # type: dict[SubType, str]
    workpath, invid, ass_paths[SubType.SJ], ass_paths[SubType.TJ] = parse_workpath(sysargs.work_path)  # full path
    if Paths.RING: print('\n使用提示音：', Paths.RING.replace('/', '\\'))
    print('\n使用X264参数：', Args.ARGSX264)
    print('\n使用QAAC参数：', Args.ARGSQAAC)

    print('\n配置解析结果：')
    print('工作目录：', Paths.ROOT_FOLDER)

    # 是否不填加字幕（需要二压）
    NO_ASS_SJ = has_img(ass_paths[SubType.SJ])
    NO_ASS_TJ = has_img(ass_paths[SubType.TJ])
    isolated_noass_subtasks = []
    if NO_ASS_SJ or NO_ASS_TJ:
        Args.TASKS, isolated_noass_subtasks = organize_tasks(Args.TASKS, NO_ASS_SJ, NO_ASS_TJ)
        print('压制任务：（需要二压，已调整压制任务顺序！）')
    else:
        print('压制任务：')

    for i, task in enumerate(Args.TASKS):
        print(f'{i + 1}. ' + ' '.join(task))

    print('\n使用VS脚本模版：\n' + '\n'.join(f'{j}：{Paths.TemplatePaths[j]}' for task in Args.TASKS for j in task))

    invidname = os.path.basename(invid)
    invidname_noext = os.path.splitext(os.path.basename(invidname))[0]

    ep = parse_vidname(invidname)
    print('\n输入文件夹解析结果：', '\n视频：', os.path.basename(invid), '\n简日字幕：', os.path.basename(ass_paths[SubType.SJ]) or '无', '\n繁日字幕：', os.path.basename(ass_paths[SubType.TJ]) or '无', '\n集数：', ep)

    anime_name, anime_folder = prompt_for_animefolder()

    subfoldername = get_subfoldername(anime_name, ep)  # 含集数的文件夹
    subfolder = os.path.join(anime_folder, subfoldername)
    os.makedirs(subfolder, exist_ok=True)
    print('\n成片将保存至')
    print(subfolder)

    M4A_TMP = os.path.join(TMP, f'{invidname_noext}_m4a.m4a')
    aud = M4A_TMP

    task_runners = []
    for task in Args.TASKS:
        subtasks = []
        for s in task:
            resl, subtype, noass = parse_subtaskname(s)

            if noass:
                # 需要二压
                # 720的输入应该改成1080的输出
                outvid_1080, _ = get_avail_outvidname(subfolder, anime_name, ep, '1080', subtype, add_prefix_on_exists=False)
                # 检查是否存在对应的1080任务，或存在对应的1080成片
                if s in isolated_noass_subtasks and not os.path.exists(outvid_1080):
                    raise AssertionError('错误！需要二压，但' + s + '任务不存在1080版任务或成片！')

                subtask = Subtask(s, invidname_noext, outvid_1080, aud, subfolder, anime_name, ep, asssrc_path=None)
            else:
                asssrc_path = ass_paths[subtype]
                subtask = Subtask(s, invidname_noext, invid, aud, subfolder, anime_name, ep, asssrc_path)
            print(subtask.outvidname)
            subtasks.append(subtask)
        task_runners.append(Task(subtasks))

    if not (SKIPAUD and os.path.exists(aud)):
        log('提取音频并转码为m4a...')
        logger_file = initFileLogger('audio')
        with open(Paths.TemplatePaths.audio, 'r', encoding='utf8') as f:
            template_audio = f.read()
        tmpprefix = f'{invidname_noext}_audio'
        script_audio_tmp = get_script_tmp_path(tmpprefix)
        proc_audio(invid, aud, template_audio, script_audio_tmp, logger_file)

    st = time.time()
    [task_runner.start() for task_runner in task_runners]
    [task_runner.join() for task_runner in task_runners]
    log('全部结束，共耗时', sec2hms((time.time() - st)))


class Subtask:
    def __init__(self, subtask_str, invidname_noext, invid, aud, subfolder, anime_name, ep, asssrc_path=None):
        resl, subtype, noass = parse_subtaskname(subtask_str)
        subtaskname = f'{resl}{subtype.value}'  # 1080chs
        prefix_tmp = f'{invidname_noext}_{subtaskname}'

        self.invid = invid
        self.aud = aud

        self.asstmp_path = None
        if not noass:
            asstmp_path = os.path.join(TMP, f'{prefix_tmp}_ass.ass')
            shutil.copyfile(asssrc_path, asstmp_path)
            self.asstmp_path = asstmp_path

        self.resl = resl
        self.subtype = subtype
        self.outvid, self.outvidname = get_avail_outvidname(subfolder, anime_name, ep, resl, subtype, add_prefix_on_exists=True)
        self.vs_tmp_path = get_vs_tmp_path(prefix_tmp)
        self.script_tmp_path = get_script_tmp_path(prefix_tmp)
        self.prefix = subtaskname + ':'
        with open(Paths.TemplatePaths[subtaskname], 'r', encoding='utf8') as f:
            self.template = f.read()
        self.logger_file = initFileLogger(subtaskname)

    def run(self):
        st = time.time()
        log('生成' + self.subtype.simp_name() + self.resl + 'p...', prefix=self.prefix)
        proc_video(self.invid,
                   self.aud,
                   self.resl,
                   self.outvid,
                   self.template,
                   self.vs_tmp_path,
                   self.script_tmp_path,
                   prefix=self.prefix,
                   logger_file=self.logger_file,
                   ass=self.asstmp_path)
        log('已输出至', self.outvid, prefix=self.prefix)
        log('耗时', sec2hms((time.time() - st)), prefix=self.prefix)


class Task(threading.Thread):
    def __init__(self, subtasks: list[Subtask]):
        self.subtasks = subtasks
        super(Task, self).__init__()

    def run(self) -> None:
        for subtask in self.subtasks:
            subtask.run()


if __name__ == '__main__':
    try:
        main()
    except CalledProcessError as err:
        if DEBUGMODE:
            traceback.print_exc()
        else:
            print(err.stderr.decode('utf8'))
            print('\n外部程序执行报错！请检查报错信息，或将问题提交到 https://github.com/zhimengsub/compresser/issues')
    except (FileNotFoundError, AssertionError, PlaysoundException) as err:
        print()
        print(err)
    except Exception as err:
        traceback.print_exc()
        print('\n发生了未知错误！请将上面的报错信息提交到 https://github.com/zhimengsub/compresser/issues')
    else:
        log('成功！')
        playring()
    finally:
        if PURGETMP:
            for name in os.listdir(TMP):
                os.remove(os.path.join(TMP, name))
            os.removedirs(TMP)

        if PAUSE:
            print()
            os.system('pause')