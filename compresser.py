import os
import shutil
import subprocess
import threading
import time
import traceback
from logging import Logger
from subprocess import CalledProcessError, PIPE

from playsound import playsound, PlaysoundException

from utils.conf import Args, load_conf
from utils.consts import *
from utils.logger import initFileLogger
from utils.misc import log, parse_workpath, parse_vidname, get_animefolder_from_input, get_subfoldername, sec2hms, \
    parse_jobname, log_process, has_img, organize_tasks, get_avail_outvidname, get_vs_tmp, get_script_tmp
from utils.paths import TMP, Paths
from utils.subtype import SubType

VER = 'v2.0.6'
DESCRIPTION = '************************************************************************************\n' + \
              '* 织梦字幕组自动压制工具\n' + \
              '* —— ' + VER + ' by 谢耳朵w\n*\n' + \
              '* 使用说明、获取最新版本、提交建议和错误请前往 https://github.com/zhimengsub/compresser\n' + \
              '************************************************************************************'


# 音频处理
def proc_audio(invid, outaud):
    # ffmpeg 提取音频，转码至m4a
    cmdffmpeg = f'"{Paths.FFMPEG}" -y -i "{invid}" -vn -c:a aac "{outaud}"'
    log(cmdffmpeg)
    subprocess.run(cmdffmpeg, check=True, stdout=PIPE, stderr=PIPE)

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
        try:
            x264 = subprocess.run(cmdx264, stdin=vspipe.stdout, stdout=PIPE, stderr=PIPE)
        finally:
            if logger_file:
                logger_file.debug('')
                log_process(logger_file, cmdx264, x264)
        vspipe.stdout.close()
        vspipe.stderr.close()

    # 与m4a音频封装
    log('封装音频中...', prefix=prefix)
    cmdffmpeg = f'"{Paths.FFMPEG}" -y -i "{vs_tmp}" -i "{inaud}" -c:v copy -c:a copy -map 0:v:0 -map 1:a:0 "{outvid}"'
    log(cmdffmpeg, prefix=prefix)
    try:
        ffmpeg = subprocess.run(cmdffmpeg, check=True, stdout=PIPE, stderr=PIPE)
    finally:
        if logger_file:
            logger_file.debug('')
            log_process(logger_file, cmdffmpeg, ffmpeg)

def playring():
    if os.path.exists(Paths.RING):
        playsound(Paths.RING)

def main():
    global workpath, M4A_TMP
    print(DESCRIPTION)

    load_conf()
    asses = {}  # type: dict[SubType, str]
    workpath, invid, asses[SubType.SJ], asses[SubType.TJ] = parse_workpath()  # full path
    if Paths.RING: print('\n使用提示音', Paths.RING.replace('/', '\\'))
    print('\n使用X264参数', Args.ARGSX264)

    NO_ASS_SJ = has_img(asses[SubType.SJ])
    NO_ASS_TJ = has_img(asses[SubType.TJ])
    if NO_ASS_SJ:
        Args.TASKS, isolated = organize_tasks(Args.TASKS, NO_ASS_SJ, NO_ASS_TJ)
        assert not isolated, '错误！需要二压，但' + ', '.join(isolated) + '任务不存在1080版本！'

    print('\n配置解析结果：', '\n工作目录：', Paths.ROOT_FOLDER, '\n压制任务：')
    for i, task in enumerate(Args.TASKS):
        print(f'{i+1}. ' + ' '.join(task))

    if NO_ASS_SJ or NO_ASS_TJ:
        print('（需要二压，已调整压制任务顺序！）')

    print('\n使用VS脚本模版：\n' + '\n'.join(f'{j}：{Paths.TemplatePaths[j]}' for task in Args.TASKS for j in task))

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

    aud = M4A_TMP
    if not (SKIPAUD and os.path.exists(aud)):
        log('提取音频并转码为m4a...')
        proc_audio(invid, aud)

    task_runners = []
    for task in Args.TASKS:
        jobs = []
        for j in task:
            resl, subtype, noass = parse_jobname(j)
            jobname = f'{resl}{subtype.value}'
            tmpprefix = f'{invidname_noext}_{jobname}'
            if noass:
                # 720的invid应该改成1080的outvid
                outvid_1080 = get_avail_outvidname(subfolder, subfoldername, '1080', subtype)
                job = Job(jobname, tmpprefix, outvid_1080, aud, resl, subtype, subfolder, subfoldername, ass=None)
            else:
                ass = asses[subtype]
                asstmp = os.path.join(TMP, f'{tmpprefix}_ass.ass')
                shutil.copyfile(ass, asstmp)
                job = Job(jobname, tmpprefix, invid, aud, resl, subtype, subfolder, subfoldername, ass=asstmp)
            jobs.append(job)
        task_runners.append(TaskRunner(jobs))

    st = time.time()
    [task_runner.start() for task_runner in task_runners]
    [task_runner.join() for task_runner in task_runners]
    log('全部结束，共耗时', sec2hms((time.time() - st)))


class Job:
    def __init__(self, jobname, tmpprefix, invid, aud, resl:str, subtype: SubType, subfolder, subfoldername, ass=None):
        self.invid = invid
        self.aud = aud
        self.ass = ass
        self.resl = resl
        self.subtype = subtype
        self.outvid = get_avail_outvidname(subfolder, subfoldername, resl, subtype)
        self.vs_tmp = get_vs_tmp(tmpprefix)
        self.script_tmp = get_script_tmp(tmpprefix)
        self.prefix = jobname + ':'
        with open(Paths.TemplatePaths[jobname], 'r', encoding='utf8') as f:
            self.template = f.read()
        self.logger_file = initFileLogger(jobname)

    def run(self):
        st = time.time()
        log('生成' + self.subtype.simp_name() + self.resl + 'p...', prefix=self.prefix)
        proc_video(self.invid, self.aud, self.resl, self.outvid, self.template, self.vs_tmp, self.script_tmp,
                   prefix=self.prefix, logger_file=self.logger_file, ass=self.ass)
        log('已输出至', self.outvid, prefix=self.prefix)
        log('耗时', sec2hms((time.time() - st)), prefix=self.prefix)


class TaskRunner(threading.Thread):
    def __init__(self, tasks: list[Job]):
        self.tasks = tasks
        super(TaskRunner, self).__init__()

    def run(self) -> None:
        for task in self.tasks:
            task.run()


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