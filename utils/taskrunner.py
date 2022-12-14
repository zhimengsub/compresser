import os.path
import threading
import time
import traceback

from utils.conf import Args
from utils.logger import initFileLogger
from utils.mainutils import proc_video
from utils.misc import get_avail_outvidname, sec2hms, log
from utils.paths import TMP, Paths
from utils.subtype import SubType


class Job:
    def __init__(self, jobname, tmpprefix, invid, aud, ass, resl:str, subtype: SubType, subfolder, subfoldername):
        self.invid = invid
        self.aud = aud
        self.ass = ass
        self.resl = resl
        self.subtype = subtype
        self.outvid = get_avail_outvidname(subfolder, subfoldername, resl, subtype)
        self.vs_tmp = os.path.join(TMP, f'{tmpprefix}_vs'+Args.Suffxies.x264_output)
        self.script_tmp = os.path.join(TMP, f'{tmpprefix}_script.vpy')
        self.prefix = jobname + ':'
        with open(Paths.TemplatePaths[jobname], 'r', encoding='utf8') as f:
            self.template = f.read()
        self.logger_file = initFileLogger(jobname)

    def run(self):
        st = time.time()
        self.proc_video()
        log('耗时', sec2hms((time.time() - st)), prefix=self.prefix)

    def proc_video(self):
        log('生成'+self.subtype.simp_name()+self.resl+'p...', prefix=self.prefix)
        proc_video(self.invid, self.aud, self.ass, self.resl, self.outvid, self.template, self.vs_tmp, self.script_tmp, prefix=self.prefix, logger_file=self.logger_file)
        log('已输出至', self.outvid, prefix=self.prefix)


class TaskRunner(threading.Thread):
    def __init__(self, tasks: list[Job]):
        self.tasks = tasks
        super(TaskRunner, self).__init__()

    def run(self) -> None:
        for task in self.tasks:
            task.run()
