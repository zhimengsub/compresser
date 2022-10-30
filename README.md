# 织梦字幕组自动压制脚本

准备好1080p原片、简日字幕、繁日字幕，会自动调用工具压制出1080p和720p成片。

## 程序下载

在[Releases](https://github.com/zhimengsub/compresser/releases)页面选择最新版本的程序下载。

## 使用说明

1. 编辑配置文件`conf.ini`（首次运行时双击运行`compresser.exe`后会在同一目录下生成）

   示例：
   ```ini
   [TOOLS]
   ; 配置各工具目录
   ffmpeg = D:\Software\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe
   vspipe = D:\Software\VapourSynth\VapourSynth64Portable\VapourSynth64\VSPipe.exe
   x264 = D:\Software\VapourSynth\VapourSynth64Portable\bin\x264.exe
   qaac = D:\Software\MeGUI\MeGUI-2913-32\tools\qaac\qaac.exe
   
   [PATHS]
   ; 配置输出文件的根目录（具体作用见第4步）
   root_folder = D:\Animes
   ; (可选) 定义结束提示音文件的目录(相对路径或绝对路径)，等号右侧值为空则关闭提示音。
   hint = src\ring.mp3
   ; (可选) 定义VS脚本模版的目录(相对或绝对路径)，
   ;   注意不是普通vpy脚本，请参考src/template.vpy中2～5行设置输入路径和成片分辨率变量。
   template = src\template.vpy
   
   [ARG_TEMPLATES]
   ; (可选) 定义X264参数。注意-o参数必须为"{VS_TMP}" (含引号)
   x264 = --demuxer y4m --preset slower --ref 4 --merange 24 --me umh --bframes 10 --aq-mode 3 --aq-strength 0.7 --deblock 0:0 --trellis 2 --psy-rd 0.6:0.1 --crf 21 --output-depth 8 - -o "{VS_TMP}"
   
2. 准备原片文件夹
   
    其中包含一个`.mkv`/`.mp4`视频，两个`.ass`字幕（简日、繁日），共三个文件。
    
    其中，视频文件名中应包含`E01`等字样表示其集数；

    繁日字幕文件名应为`<简日字幕文件名> (1).ass`。

3. 将该文件夹拖放至`compresser.exe`，即可运行程序
4. 按照程序提示配置输出文件命名格式。例如：
   
   配置文件中`root_folder = D:\Animes`，运行后会显示该目录下的文件夹作为输出目录：
   ```commandline
   请输入序号或新番全名(用于合集文件夹及成片命名):
   1. 电锯人 Chainsaw Man
   2. ...
   3. ...
   >
   ```
   如果合集文件夹已存在，输入其序号（如输入`1`），成片会保存在`<root_folder>\电锯人 Chainsaw Man\[织梦字幕组][电锯人 Chainsaw Man][01集]\`文件夹下（假设原片为第1集），分别命名为：
   - `[织梦字幕组][电锯人 Chainsaw Man][01集][AVC][简日双语][1080P].mp4`
   - `[織夢字幕組][電鋸人 Chainsaw Man][01集][AVC][繁日雙語][1080P].mp4`
   - `[织梦字幕组][电锯人 Chainsaw Man][01集][AVC][简日双语][720P].mp4`
   - `[織夢字幕組][電鋸人 Chainsaw Man][01集][AVC][繁日雙語][720P].mp4`
   
   如果为新番，输入新番**全名**（如输入`间谍过家家 SPY×FAMILY`），成片会保存在`<root_folder>\间谍过家家 SPY×FAMILY\[织梦字幕组][间谍过家家 SPY×FAMILY][01集]\`文件夹下（假设原片为第1集），分别命名为：
   - `[织梦字幕组][间谍过家家 SPY×FAMILY][01集][AVC][简日双语][1080P].mp4`
   - `[織夢字幕組][間諜過家家 SPY×FAMILY][01集][AVC][繁日雙語][1080P].mp4`
   - `[织梦字幕组][间谍过家家 SPY×FAMILY][01集][AVC][简日双语][720P].mp4`
   - `[織夢字幕組][間諜過家家 SPY×FAMILY][01集][AVC][繁日雙語][720P].mp4`

   如果已经压制过，会在输出文件名前添加`[V2]`、`[V3]`...等字样。

5. 压制完成后会播放提示音。

## 提出修改建议 / 运行时的错误和BUG

请提交[Issue](https://github.com/zhimengsub/SubtitleCleaner/issues)，需包含完整的报错信息。



# TODO

- [ ] 自定义成片命名格式
- [X] 自定义传入x264的参数
