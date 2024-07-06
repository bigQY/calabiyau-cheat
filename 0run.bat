@ echo off
%1 %2
ver|find "5.">nul&&goto :Admin
mshta vbscript:createobject("shell.application").shellexecute("%~s0","goto :Admin","","runas",1)(window.close)&goto :eof
:Admin
echo 开始执行...
call conda activate trt
S:/miniconda3/envs/trt/python.exe S:/code/klbqTensorRt/main.py
echo 执行完毕，按任意键继续...
pause