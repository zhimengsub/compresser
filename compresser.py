import os
import shutil
import time
import traceback
from subprocess import CalledProcessError
from playsound import PlaysoundException

from utils.conf import Args, load_conf, assert_conf
from utils.mainutils import playring, proc_audio
from utils.misc import log, parse_workpath, parse_vidname, get_animefolder_from_input, get_subfoldername, sec2hms, \
    parse_jobname
from utils.paths import TMP, Paths
from utils.subtype import SubType
from utils.consts import *
from utils.taskrunner import Job, TaskRunner

VER = 'v2.0.4.003'
DESCRIPTION = '************************************************************************************\n' + \
              '* 织梦字幕组自动压制工具\n' + \
              '* —— ' + VER + ' by 谢耳朵w\n*\n' + \
              '* 使用说明、获取最新版本、提交建议和错误请前往 https://github.com/zhimengsub/compresser\n' + \
              '************************************************************************************'


def main():
    global workpath, VS_TMP, M4A_TMP
    print(DESCRIPTION)

    load_conf()
    assert_conf()
    asses = {}  # type: dict[SubType, str]
    workpath, invid, asses[SubType.SJ], asses[SubType.TJ] = parse_workpath()  # full path
    if Paths.RING: print('\n使用提示音', Paths.RING.replace('/', '\\'))
    print('\n使用VS脚本模版', Paths.TEMPLATE)
    print('\n使用X264参数', Args.ARGSX264)

    print('\n配置解析结果：', '\n工作目录：', Paths.ROOT_FOLDER, '\n压制任务：')
    for i, task in enumerate(Args.TASKS):
        print(f'{i+1}. ' + ' '.join(task))

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
            resl, subtype = parse_jobname(j)
            jobname = f'{resl}{subtype.value}'
            tmpprefix = f'{invidname_noext}_{jobname}'
            ass = asses[subtype]
            asstmp = os.path.join(TMP, f'{tmpprefix}_ass.ass')
            shutil.copyfile(ass, asstmp)
            job = Job(jobname, tmpprefix, invid, aud, asstmp, resl, subtype, subfolder, subfoldername)
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
    finally:
        if PURGETMP:
            for name in os.listdir(TMP):
                os.remove(os.path.join(TMP, name))
            os.removedirs(TMP)

        if PAUSE:
            print()
            os.system('pause')