from vapoursynth import core
src=r"$src"
width=$w
height=$h
src=core.lsmas.LWLibavSource(src,repeat=True,threads=16)
src=core.resize.Lanczos(src,width,height)
src.set_output()