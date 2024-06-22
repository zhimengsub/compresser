from vapoursynth import core

src = r"$src"
audio = core.bas.Source(src)
audio.set_output(1)