
from vapoursynth import core
import mvsfunc as mvf

src=r"{src}"
ass=r"{ass}"
width={w}
height={h}

src8=core.lsmas.LWLibavSource(src,repeat=True,threads=16)

#src8 = core.vivtc.VDecimate(src8)

src16 = mvf.Depth(src8,depth=16)

nr = core.knlm.KNLMeansCL(src16, d=1, a=2, s=4, h=1.4)
debd = core.neo_f3kdb.Deband(nr,12,16,16,16)
debd = core.neo_f3kdb.Deband(debd,16,32,16,16)
us = core.resize.Lanczos(debd, width, height)

#转1080P
src8=core.resize.Lanczos(src8, width, height)
#res = mvf.Depth(us,depth=8)
#上字幕（要上就把下面句子取消注解）
#res = core.xyvsf.TextSub(res, ass)
src8 = core.vsfm.TextSubMod(src8, ass)
#src8=core.sub.TextFile(src8, ass)

#最后输出
src8.set_output()