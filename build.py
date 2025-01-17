import PyInstaller.__main__
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))
icon_path = r'E:\token\头像.ico'

PyInstaller.__main__.run([
    '星月汇聚助手.py',
    '--name=星月汇聚助手',
    '--windowed',
    f'--icon={icon_path}',
    '--onefile',
    '--clean',
    '--noconfirm',
    '--add-data', f'{icon_path};.',
    '--uac-admin',
    '--version-file=version.txt',
    '--noconsole',
]) 