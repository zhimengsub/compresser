from vapoursynth import core
import vapoursynth as vs
import mvsfunc as mvf
from math import floor
from typing import Union

source = r"$src"
asstSubMod = r"$ass"
width=$w
height=$h

def descale_cropping_args(clip: vs.VideoNode, # letterbox-free source clip
                          src_height: float,
                          base_height: int,
                          base_width: int,
                          crop_top: int = 0,
                          crop_bottom: int = 0,
                          crop_left: int = 0,
                          crop_right: int = 0,
                          mode: str = 'wh'
                          ) -> dict[str, Union[int, float]]:
    ratio = src_height / (clip.height + crop_top + crop_bottom)
    src_width = ratio * (clip.width + crop_left + crop_right)

    cropped_src_width = ratio * clip.width
    margin_left = (base_width - src_width) / 2 + ratio * crop_left
    margin_right = (base_width - src_width) / 2 + ratio * crop_right
    cropped_width = base_width - floor(margin_left) - floor(margin_right)
    cropped_src_left = margin_left - floor(margin_left)

    cropped_src_height = ratio * clip.height
    margin_top = (base_height - src_height) / 2 + ratio * crop_top
    margin_bottom = (base_height - src_height) / 2 + ratio * crop_bottom
    cropped_height = base_height - floor(margin_top) - floor(margin_bottom)
    cropped_src_top = margin_top - floor(margin_top)

    args = dict(
        width=clip.width,
        height=clip.height
    )
    args_w = dict(
        width=cropped_width,
        src_width=cropped_src_width,
        src_left=cropped_src_left
    )
    args_h = dict(
        height=cropped_height,
        src_height=cropped_src_height,
        src_top=cropped_src_top
    )
    if 'w' in mode.lower():
        args.update(args_w)
    if 'h' in mode.lower():
        args.update(args_h)
    return args

src8 = core.lsmas.LWLibavSource(source)
last16 = mvf.Depth(src8, depth=16)

y, u, v = core.std.SplitPlanes(last16)

d_args = descale_cropping_args(y, src_height=855, base_height=855, base_width=1520)
descaled = core.descale.Debilinear(y, **d_args)
f1 = 1
f2 = 1
upscaled = descaled.nnedi3.nnedi3(field=f1, dh=True).std.Transpose().nnedi3.nnedi3(field=f2, dh=True).std.Transpose()
c_args = dict(
    src_width = d_args['src_width'] * 2,
    src_height = d_args['src_height'] * 2,
    src_left = d_args['src_left'] * 2 + 0.5 - f2,
    src_top = d_args['src_top'] * 2 + 0.5 - f1
)

final= core.resize.Spline36(upscaled, width, height, **c_args)

descale = core.std.ShufflePlanes(clips=[final, u, v], planes=[0, 0, 0], colorfamily=vs.YUV)

res=core.fmtc.bitdepth(descale, bits=32)
vbasic = core.bm3dcuda.BM3D(res, radius=1).bm3d.VAggregate(radius=1, sample=1)
vfinal = core.bm3dcuda.BM3D(res, ref=vbasic, radius=1).bm3d.VAggregate(radius=1)

dbed = core.neo_f3kdb.Deband(vfinal, range=15, y=32, cb=0, cr=0, grainy=0, grainc=0, output_depth=16)
dbed = mvf.LimitFilter(dbed, vfinal, thr=0.55, elast=1.5, planes=[0, 1, 2])

noise = core.std.MakeDiff(descale,dbed)
blur = core.rgvs.RemoveGrain(dbed, 11)
diff = core.std.MakeDiff(dbed,blur)
diff = core.rgvs.Repair(diff,noise,1)
res = core.std.MergeDiff(dbed,diff)

last10 = mvf.Depth(res, depth=10)
res = core.vsfm.TextSubMod(last10, asstSubMod)

res.set_output()