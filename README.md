# 织梦字幕组自动压制脚本

准备好1080p原片、简日字幕、繁日字幕，会自动调用工具压制出1080p和720p成片。

## 程序下载

在[Releases](https://github.com/zhimengsub/compresser/releases)页面选择最新版本的程序下载。

## 使用说明

1. 编辑配置文件`conf.ini`（首次运行时双击运行`compresser.bat`后会在同一目录下生成）

   说明：（`(必改)`表示必须根据实际情况进行修改的参数，`(选改)`则表示可以不用修改）
   ```ini
   [TOOLS]
   ; (必改) 配置各工具目录（x264与x265至少配置一个）
   ffmpeg = D:\Software\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe
   mp4box = G:\Portable\小丸工具箱\xiaowan\tools\mp4box.exe
   vspipe = D:\Software\VapourSynth\VapourSynth64Portable\VapourSynth64\VSPipe.exe
   x264 = D:\Software\VapourSynth\VapourSynth64Portable\bin\x264.exe
   x265 = D:\Software\VapourSynth\VapourSynth64Portable\bin\x265.exe
   
   [PATHS]
   ; (必改) 配置输出文件的根目录（具体作用见第4步）
   root_folder = D:\Animes
   ; (选改) 定义结束提示音文件的目录(相对路径或绝对路径)，等号右侧值为空则关闭提示音。
   hint = src\ring.mp3
   
   [TemplatePaths]
   ; (选改) 定义不同任务的VS脚本模版的目录(相对或绝对路径)，
   ;   注意不是普通vpy脚本，请参考src\template.vpy中2～5行设置输入路径和成片分辨率变量。
   ;   可以为x264和x265指定不同的VS脚本模板
   720chs264 = src\template.vpy
   720cht264 = src\template.vpy
   1080chs264 = src\template 2023-11_1080P.vpy
   1080cht264 = src\template 2023-11_1080P.vpy
   720chs265 = src\template.vpy
   720cht265 = src\template.vpy
   1080chs265 = src\template 2023-11_1080P.vpy
   1080cht265 = src\template 2023-11_1080P.vpy
   ; 下面这几个是二压时用的版本，输入是已经压好的1080P成片
   720chs_noass = src\template_noass.vpy
   720cht_noass = src\template_noass.vpy
   
   [ARG_TEMPLATES]
   ; (选改) 定义x264、x265参数。注意-o参数必须为"{VS_TMP}" (含引号)
   x264 = --demuxer y4m --preset veryslow --ref 8 --merange 24 --me umh --bframes 10 --aq-mode 3 --aq-strength 0.7 --deblock 0:0 --trellis 2 --psy-rd 0.6:0.1 --crf 18.5 --output-depth 8 - -o "{VS_TMP}"
   x265 = --y4m --preset slower --frame-threads 1 --deblock -1:-1 --ctu 32 --crf 16.0 --pbratio 1.2 --cbqpoffs -2 --crqpoffs -2 --no-sao --me 3 --subme 3 --merange 44 --b-intra --no-rect --no-amp --ref 4 --weightb --keyint 360 --min-keyint 1 --bframes 6 --aq-mode 1 --aq-strength 0.8 --rd 4 --psy-rd 2.0 --psy-rdoq 3.0 --no-open-gop --rc-lookahead 80 --scenecut 40 --qcomp 0.65 --no-strong-intra-smoothing --vbv-bufsize 30000 --vbv-maxrate 28000 --output-depth 10 - -o "{VS_TMP}"
   
   [Suffixes]
   ; (选改) 修改x264、x265视频（无声音）输出格式（对应xxx_vs_output），以及封装音视频后成片的格式（对应xxx_merged_output）
   x264_vs_output = .mp4
   x264_merged_output = .mp4
   x265_vs_output = .hevc
   x265_merged_output = .mp4
   
   [OutputPattern]
   ; (选改) 修改成片的命名规则，变量部分用花括号括起来（繁体版成片命名会自动繁化）
   ; 成片所在文件夹命名，支持的变量有：
   ;    NAME: 番名（见第4步）
   ;    EP_EN: 集数，阿拉伯数字，示例："09"、"31"
   ;    EP_ZH: 集数，中文，示例："九"、"三十一"
   ; 设置参考：
   ; [织梦字幕组][{NAME}][{EP_EN}集] -> [织梦字幕组][电锯人 Chainsaw Man][01集]
   folder = [织梦字幕组][{NAME}][{EP_EN}集]
   ; 成片命名，支持的变量有（按需使用）：
   ;    NAME: 番名（见第4步）
   ;    EP_EN: 集数，阿拉伯数字，示例："09"、"31"
   ;    EP_ZH: 集数，中文，示例："九"、"三十一"
   ;    VTYPE: 视频编码器，取值："HEVC"或"AVC"，取决使用x265还是x264
   ;    BIT: 位深，取决于[ARG_TEMPLATES]中--output-depth的值
   ;    RESL: 分辨率，取值："1080"或"720"
   ;    LANG: 语言，取值："简日双语"或"繁日双语"
   ;    LANG_EN: 语言，英文，取值："CHS＆JPN"或"CHT＆JPN"
   ;    VER: 版本号，示例："V2"、"V3"（如果为V1则会连同方括号一起删除）
   ; [织梦字幕组][{NAME}][{EP_EN}集][{RESL}P][AVC][{VENC}][{LANG}] -> [织梦字幕组][电锯人 Chainsaw Man][01集][AVC][x265][简日双语][1080P]
   ; [织梦字幕组]{NAME}[{EP_EN}][第{EP_ZH}夜][GB_JP][AVC][{RESL}P] -> [织梦字幕组]与猫共度的夜晚 夜は猫といっしょ[39][第三十九夜][GB_JP][AVC][1080P]
   file = [织梦字幕组][{NAME}][{EP_EN}集][{RESL}P][AVC][{VENC}][{LANG}][{VER}]
   

   [ParallelTasks]
   ; 添加并行任务，设置分辨率、字幕语言和编码器。
   ; 分辨率：1080或720
   ; 字幕语言：chs表示简中，cht表示繁中。
   ; 编码器：264或265，必须要选其中一种
   ; 不同行之间并行执行；同一行内串行执行，用逗号隔开。
   ; 下面的代码表示依次压制1080chs和720chs，与此同时也在依次压制1080cht和720cht
   task1 = 1080chs265, 720chs264
   task2 = 1080cht265, 720cht264
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

   如果已经压制过，会在`{VER}`位置添加`V2`、`V3`...等字样。如果不含`{VER}`，则默认添加版本号在文件开头。

5. 压制完成后会播放`[PATHS]`中`hint`指定的提示音。

### 使用不同的配置文件

编辑`compresser.bat`，按里面的提示修改配置文件路径即可。

可以把bat复制多份，每一份使用不同的配置文件。

bat本体不能移动，可以创建bat的快捷方式，然后把快捷方式放置到需要的地方，文件夹直接拖放到快捷方式上即可。

## 提出修改建议 / 运行时的错误和BUG

请提交[Issue](https://github.com/zhimengsub/SubtitleCleaner/issues)，需包含完整的报错信息。



