import os.path
import threading
import time
import traceback

from utils.mainutils import proc_video
from utils.misc import get_avail_outvidname, sec2hms, log
from utils.paths import TMP, Paths
from utils.subtype import SubType


class Job:
    def __init__(self, invid, invidname_noext, aud, ass, resl:str, subtype: SubType, subfolder, subfoldername):
        name = f"{resl}{subtype.value}"
        self.invid = invid
        self.aud = aud
        self.ass = ass
        self.resl = resl
        self.subtype = subtype
        self.outvid = get_avail_outvidname(subfolder, subfoldername, resl, subtype)
        self.vs_tmp = os.path.join(TMP, f'{invidname_noext}_{name}_vs.mp4')
        self.script_tmp = os.path.join(TMP, f'{invidname_noext}_{name}_script.vpy')
        self.prefix = name + ':'
        with open(Paths.TemplatePaths[name], 'r', encoding='utf8') as f:
            self.template = f.read()

    def run(self):
        st = time.time()
        self.proc_video()
        log('耗时', sec2hms((time.time() - st)), prefix=self.prefix)

    def proc_video(self):
        log('生成'+self.subtype.simp_name()+self.resl+'p...', prefix=self.prefix)
        try:
            proc_video(self.invid, self.aud, self.ass, self.resl, self.outvid, self.template, self.vs_tmp, self.script_tmp, prefix=self.prefix)
            log('已输出至', self.outvid, prefix=self.prefix)
        except Exception as err:
            log('错误：\n'+traceback.format_exc())


class TaskRunner(threading.Thread):
    def __init__(self, tasks: list[Job]):
        self.tasks = tasks
        super(TaskRunner, self).__init__()

    def run(self) -> None:
        for task in self.tasks:
            task.run()
