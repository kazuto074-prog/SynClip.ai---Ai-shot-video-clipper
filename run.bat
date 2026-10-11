@echo off
set "PATH=C:\Users\suhai\AppData\Local\Programs\Python\Python310\Lib\site-packages\torch\lib;C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Program Files\NVIDIA Corporation\NVSMI;C:\Users\suhai\AppData\Local\Programs\Python\Python310\Scripts;C:\Users\suhai\AppData\Local\Programs\Python\Python310;%PATH%"
title SynClip.ai Studio
echo ================================================================
echo         Starting SynClip.ai Studio
echo         Hardware: NVIDIA GeForce RTX 3050 (6GB VRAM)
echo         Whisper Acceleration: CUDA cuBLAS 12 Enabled
echo ================================================================
cd /d "%~dp0"
python studio_server.py
pause
