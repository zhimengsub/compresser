@echo off
cd /d %~dp0

IF "%1"=="" (
  SET WORKPATH=""
) ELSE (
  SET WORKPATH="%1"
)

@REM 用法：
@REM 1. 配置文件的路径写在下面（填相对路径的话必须跟bat在同一目录，然后给bat新建快捷方式，就可以复制到别的地方了。bat本体的位置不要动）
@REM 如果需要使用不同的配置文件，可以复制几份不同的bat，修改下面的内容后分别运行即可
set CONF=conf.ini

@REM 2. 把要压制的文件夹拖入bat或bat的快捷方式即可
compresser.exe --work-path %WORKPATH% --conf-path %CONF%
