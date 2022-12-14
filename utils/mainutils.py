import os.path
import subprocess
from logging import Logger
from subprocess import PIPE

from playsound import playsound

from utils.conf import Args
from utils.consts import *
from utils.misc import log, log_pipe, log_process
from utils.paths import Paths


# 音频处理
def proc_audio(invid, outaud):
    # ffmpeg 提取音频，转码至m4a
    cmdffmpeg = f'"{Paths.FFMPEG}" -y -i "{invid}" -vn -c:a aac "{outaud}"'
    log(cmdffmpeg)
    subprocess.run(cmdffmpeg, check=True, stdout=PIPE, stderr=PIPE)

# 视频处理
def gen_script(template, src, ass, resl):
    assert '{src}' in template and '{ass}' in template and '{w}' in template and '{h}' in template, 'vpy脚本不符合要求！请参考`src/template.vpy`中2～5行设置输入路径和成片分辨率变量！'
    w = '1920' if resl == '1080' else '1280'
    h = '1080' if resl == '1080' else '720'
    return template.format(src=src, ass=ass, w=w, h=h)

def proc_video(invid, inaud, ass, resl, outvid, template, vs_tmp, script_tmp, prefix='', logger_file:Logger=None):
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
    cmdffmpeg = f'"{Paths.FFMPEG}" -y -i "{vs_tmp}" -i "{inaud}" -map 0:v -map 1:a -c:v copy -c:a copy "{outvid}"'
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