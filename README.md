# 织梦字幕组自动压制脚本

准备好1080p原片、简日字幕、繁日字幕，会自动调用工具压制出1080p和720p成片。

## 程序下载

在[Releases](https://github.com/zhimengsub/compresser/releases)页面选择最新版本的程序下载。

## 使用说明

1. 编辑配置文件`conf.ini`（首次运行时双击运行`compresser.bat`后会在同一目录下生成）

   说明：（`(必须)`表示必须根据实际情况进行修改的参数，`(可选)`则表示可以不用修改）
   ```ini
   [TOOLS]
   ; (必须) 配置各工具目录
   ffmpeg = D:\Software\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe
   vspipe = D:\Software\VapourSynth\VapourSynth64Portable\VapourSynth64\VSPipe.exe
   x264 = D:\Software\VapourSynth\VapourSynth64Portable\bin\x264.exe
   qaac = D:\Software\MeGUI\MeGUI-2913-32\tools\qaac\qaac.exe
   
   [PATHS]
   ; (必须) 配置输出文件的根目录（具体作用见第4步）
   root_folder = D:\Animes
   ; (可选) 定义结束提示音文件的目录(相对路径或绝对路径)，等号右侧值为空则关闭提示音。
   hint = src\ring.mp3
   
   [TemplatePaths]
   ; (可选) 定义不同任务的VS脚本模版的目录(相对或绝对路径)，
   ;   注意不是普通vpy脚本，请参考src\template.vpy中2～5行设置输入路径和成片分辨率变量。
   720chs = src\template.vpy
   720cht = src\template.vpy
   1080chs = src\template2.vpy
   1080cht = src\template2.vpy
   ; 下面这几个不要修改
   720chs_noass = src\template_noass.vpy
   720cht_noass = src\template_noass.vpy
   audio = src\template_audio.vpy
   
   [ARG_TEMPLATES]
   ; (可选) 定义X264参数。注意-o参数必须为"{VS_TMP}" (含引号)
   x264 = --demuxer y4m --preset veryslow --ref 8 --merange 24 --me umh --bframes 10 --aq-mode 3 --aq-strength 0.7 --deblock 0:0 --trellis 2 --psy-rd 0.6:0.1 --crf 18.5 --output-depth 8 - -o "{VS_TMP}"
   ; (可选) 定义QAAC参数。注意-o参数必须为"{VS_TMP}" (含引号)
   qaac = --ignorelength --threading -V 91 --no-delay - -o "{M4A_TMP}"
   
   [Suffixes]
   ; (可选) 修改x264输出或封装音视频后成片的格式
   x264_output = .mp4
   merged_output = .mp4
   
   [OutputPattern]
   ; (可选) 修改成片的命名规则，变量部分用花括号括起来（繁体版成片命名也会自动繁化）
   ; 成片所在文件夹命名，支持的变量有：
   ;    NAME: 番名（见第4步）
   ;    EP_EN: 集数，阿拉伯数字，示例："09"、"31"
   ;    EP_ZH: 集数，中文，示例："九"、"三十一"
   ; 设置参考：
   ; [织梦字幕组][{NAME}][{EP_EN}集] -> [织梦字幕组][电锯人 Chainsaw Man][01集]
   folder = [织梦字幕组][{NAME}][{EP_EN}集]
   ; 成片命名，支持的变量有：
   ;    NAME: 番名（见第4步）
   ;    EP_EN: 集数，阿拉伯数字，示例："09"、"31"
   ;    EP_ZH: 集数，中文，示例："九"、"三十一"
   ;    RESP: 分辨率，取值："1080"或"720"
   ;    LANG: 语言，取值："简日双语"或"番日双语"
   ; [织梦字幕组][{NAME}][{EP_EN}集][{RESL}P][AVC][{LANG}] -> [织梦字幕组][电锯人 Chainsaw Man][01集][AVC][简日双语][1080P]
   ; [织梦字幕组]{NAME}[{EP_EN}][第{EP_ZH}夜][GB_JP][AVC][{RESL}P] -> [织梦字幕组]与猫共度的夜晚 夜は猫といっしょ[39][第三十九夜][GB_JP][AVC][1080P]
   file = [织梦字幕组][{NAME}][{EP_EN}集][{RESL}P][AVC][{LANG}]

   [ParallelTasks]
   ; 添加并行任务，设置分辨率和字幕语言。
   ; chs表示简中，cht表示繁中。
   ; 不同行之间并行执行；同一行内串行执行，用逗号隔开。
   ; 下面的代码表示依次压制1080chs和720chs，与此同时也在依次压制1080cht和720cht
   task1 = 1080chs, 720chs
   task2 = 1080cht, 720cht
   ; 下面的代码同时压制所有任务
   ; task1 = 1080chs
   ; task2 = 1080cht
   ; task3 = 720chs
   ; task4 = 720cht

   ```
2. 准备原片文件夹
   
    其中包含一个`.mkv`/`.mp4`视频，两个`.ass`字幕（简日、繁日），共三个文件。
    
    其中，视频文件名中应包含`E01`等字样表示其集数；

    繁日字幕文件名应为`<简日字幕文件名> (1).ass`。

3. 将该文件夹拖放至`compresser.bat`，即可运行程序（注意不要拖放到`compresser.exe`）
4. 按照程序提示配置输出文件命名格式。例如：
   
   运行后，会显示`root_folder`目录下的各个文件夹作为输出目录。
  
   示例：当前`D:\Animes`目录下包含一个文件夹`电锯人 Chainsaw Man`，运行程序后会显示：
   ```commandline
   请输入序号或新番全名(用于合集文件夹及成片命名):
   1. 电锯人 Chainsaw Man
   >
   ```
   如果想保存在`电锯人 Chainsaw Man`中，则直接输入`1`，成片则会保存在`D:\Animes\电锯人 Chainsaw Man\[织梦字幕组][电锯人 Chainsaw Man][01集]\`文件夹下（假设原片为第1集），分别命名为：
   - `[织梦字幕组][电锯人 Chainsaw Man][01集][AVC][简日双语][1080P].mp4`
   - `[織夢字幕組][電鋸人 Chainsaw Man][01集][AVC][繁日雙語][1080P].mp4`
   - `[织梦字幕组][电锯人 Chainsaw Man][01集][AVC][简日双语][720P].mp4`
   - `[織夢字幕組][電鋸人 Chainsaw Man][01集][AVC][繁日雙語][720P].mp4`
   
   如果是新番，输入新番**全名**（如输入`间谍过家家 SPY×FAMILY`），则成片会保存在`D:\Animes\间谍过家家 SPY×FAMILY\[织梦字幕组][间谍过家家 SPY×FAMILY][01集]\`文件夹下（假设原片为第1集），分别命名为：
   - `[织梦字幕组][间谍过家家 SPY×FAMILY][01集][AVC][简日双语][1080P].mp4`
   - `[織夢字幕組][間諜過家家 SPY×FAMILY][01集][AVC][繁日雙語][1080P].mp4`
   - `[织梦字幕组][间谍过家家 SPY×FAMILY][01集][AVC][简日双语][720P].mp4`
   - `[織夢字幕組][間諜過家家 SPY×FAMILY][01集][AVC][繁日雙語][720P].mp4`
   
   （以上示例的成片命名前提是`[OutputPattern]`配置为默认值）

   如果已经压制过，会在输出文件名前添加`[V2]`、`[V3]`...等字样。

5. 压制完成后会播放`[PATHS]`中`hint`指定的提示音。

### 使用不同的配置文件

编辑`compresser.bat`，按里面的提示修改配置文件路径即可。

可以把bat复制多份，每一份使用不同的配置文件。

bat本体不能移动，可以创建bat的快捷方式，然后把快捷方式放置到需要的地方，文件夹直接拖放到快捷方式上即可。

## 提出修改建议 / 运行时的错误和BUG

请提交[Issue](https://github.com/zhimengsub/SubtitleCleaner/issues)，需包含完整的报错信息。



# TODO

- [x] 自定义成片命名格式
- [X] 自定义传入x264的参数
