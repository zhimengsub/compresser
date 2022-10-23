from vapoursynth import core
src=r"{src}"
ass=r"{ass}"
width={w}
height={h}
src=core.lsmas.LWLibavSource(src,repeat=True,threads=16)
src=core.resize.Lanczos(src,width,height)
src=core.vsfm.TextSubMod(src,ass)
src.set_output()