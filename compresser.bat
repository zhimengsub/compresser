@echo off
cd /d %~dp0

IF "%1"=="" (
  SET WORKPATH=""
) ELSE (
  SET WORKPATH="%1"
)

@REM �÷���
@REM 1. �����ļ���·��д�����棨�����·���Ļ������bat��ͬһĿ¼��Ȼ���bat�½���ݷ�ʽ���Ϳ��Ը��Ƶ���ĵط��ˡ�bat�����λ�ò�Ҫ����
@REM �����Ҫʹ�ò�ͬ�������ļ������Ը��Ƽ��ݲ�ͬ��bat���޸���������ݺ�ֱ����м���
set CONF=conf.ini

@REM 2. ��Ҫѹ�Ƶ��ļ�������bat��bat�Ŀ�ݷ�ʽ����
compresser.exe --work-path %WORKPATH% --conf-path %CONF%
