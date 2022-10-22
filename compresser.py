import enum
import re
import sys
import os
import configparser
import subprocess
from subprocess import PIPE, CalledProcessError
import traceback
import time

VER = 'v1.0.0'
DESCRIPTION = '织梦字幕组自动压制工具\n' + \
              '—— ' + VER + ' by 谢耳朵w\n\n' + \
              '使用说明、获取最新版本、提交建议和错误请前往 https://github.com/zhimengsub/compresser'

ISEXE = hasattr(sys, 'frozen')
BASE = os.path.dirname(sys.executable if ISEXE else __file__)  # exe/py所在路径
BASE_TMP = sys._MEIPASS if ISEXE else BASE  # 打包后运行时系统tmp所在路径
TEMPLATE = os.path.join(BASE_TMP, 'template.vpy')
TMP = os.path.join(BASE, 'tmp')
os.makedirs(TMP, exist_ok=True)
SCRIPT_TMP = os.path.join(TMP, 'script.vpy')
M4A_TMP = os.path.join(TMP, 'm4a.m4a')
VS_TMP = os.path.join(TMP, 'VS.mp4')
FFMPEG = ''
VSPIPE = ''
X264 = ''
CONF = os.path.join(BASE, 'conf.ini')

ROOT_FOLDER = ''

KEY_TOOLS = 'TOOLS'
KEY_PATHS = 'PATHS'

# for debug
DEBUG = hasattr(sys, 'gettrace') and sys.gettrace() is not None
DEBUGMODE = False
SKIPAUD = False
SKIPVSTMP = False
PURGETMP = True
PAUSE = True

conf = configparser.ConfigParser()

def log(*args, **kwargs):
    t = '['+time.strftime('%H:%M:%S', time.localtime())+']'
    print()
    print(t, *args, **kwargs)

class SubType(enum.Enum):
    SJ = '简日双语'
    TJ = '繁日双语'

def load_conf():
    global FFMPEG
    global VSPIPE
    global X264
    global ROOT_FOLDER
    # default demo
    conf[KEY_TOOLS] = {
        'ffmpeg': r"D:\Software\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe",
        'VSPipe': r"D:\Software\VapourSynth\VapourSynth64Portable\VapourSynth64\VSPipe.exe",
        'x264': r"D:\Software\VapourSynth\VapourSynth64Portable\bin\x264.exe",
        'qaac': r"D:\Software\MeGUI\MeGUI-2913-32\tools\qaac\qaac.exe",
    }
    conf[KEY_PATHS] = {
        'root_folder': r"D:\animes"
    }

    if not os.path.exists(CONF):
        with open(CONF, 'w', encoding='utf8') as f:
            conf.write(f)
        raise FileNotFoundError('已生成配置文件 '+CONF+'\n\n请编辑后重新运行本程序！')

    conf.read(CONF, 'utf8')
    FFMPEG = conf[KEY_TOOLS]['ffmpeg']
    VSPIPE = conf[KEY_TOOLS]['VSPipe']
    X264 = conf[KEY_TOOLS]['x264']
    ROOT_FOLDER = conf[KEY_PATHS]['root_folder']

def assert_conf():
    # assert config files
    for sec in conf.sections():
        for name, path in conf[sec].items():
            assert os.path.exists(path), '错误！无法找到 [' + sec + '] ' + name + ' 路径 '+path+'，请重新配置conf.ini对应项。'

# 获取输入
def parse_workpath():
    if len(sys.argv) < 2:
        raise FileNotFoundError('请将待处理文件夹拖放到本程序上！')
    elif not os.path.exists(sys.argv[1]):
        raise FileNotFoundError('待处理文件夹格式错误！输入为'+sys.argv[1])
    workpath = sys.argv[1]
    folder = os.path.basename(workpath)
    vid = ''
    assS = ''
    assT = ''
    assert len(os.listdir(workpath)) == 3, '待处理文件夹内容不符合规范，应包含三个文件，一个.mkv，两个.ass。'
    for file in os.listdir(workpath):
        full = os.path.join(workpath, file)
        if file.endswith('mkv'):
            vid = full
        elif file.endswith('(1).ass'):
            assT = full
        else:
            assS = full
    assert vid and assS and assT, '待处理文件夹内容不符合规范，应包含三个文件，一个.mkv，一个xx.ass，一个xx (1).ass。'
    return folder, vid, assS, assT

def get_animefolder_from_input():
    # 读取已存在的番，输入序号，或者新番输入番名
    if DEBUG or DEBUGMODE:
        anime_name = '测试'
    else:
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
    subprocess.run([FFMPEG, '-y', '-i', invid, '-vn', '-c:a', 'aac', outaud], check=True, stdout=PIPE, stderr=PIPE)

# 视频处理
def gen_script(template, src, ass, resl):
    w = '1920' if resl == '1080' else '1280'
    h = '1080' if resl == '1080' else '720'
    return template.format(src=src, ass=ass, w=w, h=h)

def proc_video(invid, inaud, ass, resl, outvid, template):
    if not ((DEBUG or SKIPVSTMP) and os.path.exists(VS_TMP)):
        # 生成vpy
        script = gen_script(template, invid, ass, resl)
        with open(SCRIPT_TMP, 'w', encoding='utf8') as f:
            f.write(script)
        # VS压制视频字幕
        args='--demuxer y4m --preset slower --ref 4 --merange 24 --me umh --bframes 10 --aq-mode 3 --aq-strength 0.7 --deblock 0:0 --trellis 2 --psy-rd 0.6:0.1 --crf 21 --output-depth 8 -'.split(' ')
        print('VS+x264压制中...')
        vspipe = subprocess.Popen([VSPIPE, SCRIPT_TMP, '-c', 'y4m', '-'], stdout=PIPE, stderr=PIPE)
        x264 = subprocess.run([X264, *args, '-o', VS_TMP], stdin=vspipe.stdout, check=True, stdout=PIPE, stderr=PIPE)
        vspipe.stdout.close()

    # 与m4a音频封装
    print('封装音频中...')
    subprocess.run([FFMPEG, '-y', '-i', VS_TMP, '-i', inaud, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy', outvid], check=True, stdout=PIPE, stderr=PIPE)

def parse_vidname(vidname):
    res = re.search('E(\d+)', vidname)
    ep = int(res[1])
    return ep

def get_subfoldername(anime_name, ep):
    pref = '[织梦字幕组]'
    res = pref + '[' + anime_name + '][' + '{:02d}'.format(ep) + '集]'
    return res

def get_outvidname(subfoldername, resl, subtype):
    mid = '[AVC]'
    res = subfoldername + '[' + resl + 'P]' + mid + '[' + subtype.value + '].mp4'
    return res

def main():
    global workpath
    print(DESCRIPTION)

    load_conf()
    infolder, invid, assS, assT = parse_workpath()
    invidname = os.path.basename(invid)
    assert_conf()

    ep = parse_vidname(invidname)
    log('解析到集数为', ep)
    print()

    anime_name, anime_folder = get_animefolder_from_input()

    subfoldername = get_subfoldername(anime_name, ep)  # 含集数的文件夹
    subfolder = os.path.join(anime_folder, subfoldername)
    os.makedirs(subfolder, exist_ok=True)
    print('\n成片将保存至', subfolder)

    aud = M4A_TMP
    if not ((DEBUG or SKIPAUD) and os.path.exists(aud)):
        log('提取音频并转码为m4a...')
        proc_audio(invid, aud)

    with open(TEMPLATE, 'r', encoding='utf8') as f:
        template = f.read()

    # 简体1080p
    log('生成简体1080p...')
    resl = '1080'
    subtype = SubType.SJ
    outvidname = get_outvidname(subfoldername, resl, subtype)
    outvid = os.path.join(subfolder, outvidname)
    proc_video(invid, aud, assS, resl, outvid, template)
    print('\n已输出至', outvid)

    # 繁体1080p
    log('生成繁体1080p...')
    resl = '1080'
    subtype = SubType.TJ
    outvidname = get_outvidname(subfoldername, resl, subtype)
    outvid = os.path.join(subfolder, outvidname)
    proc_video(invid, aud, assT, resl, outvid, template)
    print('\n已输出至', outvid)

    # 简体720p
    log('生成简体720p...')
    resl = '720'
    subtype = SubType.SJ
    outvidname = get_outvidname(subfoldername, resl, subtype)
    outvid = os.path.join(subfolder, outvidname)
    proc_video(invid, aud, assS, resl, outvid, template)
    print('\n已输出至', outvid)

    # 繁体720p
    log('生成繁体720p...')
    resl = '720'
    subtype = SubType.TJ
    outvidname = get_outvidname(subfoldername, resl, subtype)
    outvid = os.path.join(subfolder, outvidname)
    proc_video(invid, aud, assT, resl, outvid, template)
    print('\n已输出至', outvid)


if __name__ == '__main__':
    try:
        main()
        log('成功！')
    except CalledProcessError as err:
        if DEBUG or DEBUGMODE:
            traceback.print_exc()
        else:
            print(err.stderr.decode('utf8'))
            print('\n外部程序执行报错！请检查报错信息，或将问题提交到 https://github.com/zhimengsub/compresser/issues')
    except FileNotFoundError as err:
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