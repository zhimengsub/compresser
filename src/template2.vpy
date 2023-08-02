
from vapoursynth import core
import mvsfunc as mvf

src=r"{src}"
ass=r"{ass}"
width={w}
height={h}

src=core.lsmas.LWLibavSource(src,repeat=True,threads=16)


src = mvf.Depth(src,depth=16)

src = core.knlm.KNLMeansCL(src, d=1, a=2, s=4, h=1.4)
src = core.neo_f3kdb.Deband(src,12,16,16,16)
src = core.neo_f3kdb.Deband(src,16,32,16,16)
src = core.resize.Lanczos(src, width, height)

#转1080P
res = mvf.Depth(src,depth=8)
#上字幕（要上就把下面句子取消注解）
src = core.vsfm.TextSubMod(src, ass)

#最后输出
src.set_output()