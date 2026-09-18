# 轻投屏 · SimpleAirPlay

一个简单的中文 Windows AirPlay 接收控制器，将 iPhone / iPad 屏幕镜像到电脑。

A small Chinese-language Windows controller for the open-source UxPlay AirPlay receiver. The controller is written in Python/Tkinter; it does not implement the AirPlay protocol itself.

## 功能

- 开始 / 停止接收，关闭控制器时停止其接收进程。
- 自定义设备名称。
- 请求 720p/30、1080p/60、1440p/60 或 4K/30；默认 1440p/60。
- Direct3D 11 全屏显示，保持原始比例；可切换窗口模式。
- 自动选择解码器，可启用软件 H.264 解码兼容模式。
- 保存偏好设置、按次生成视频诊断日志。
- 接收期间暂时设置引擎参数和显示偏好，停止时恢复之前的值。

## 环境

- Windows 11 x64（其他系统 / 架构未测试）。
- Python 3.14 x64，包含 Tkinter；开发时使用 Python 3.14.2。
- Bonjour Service 已安装并运行。本项目不会自动安装服务或修改防火墙。
- iPad 和电脑处于可互访的同一局域网；电脑可通过网线连接。

## 从源码运行

在项目目录打开 PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
powershell -NoProfile -File .\scripts\setup-engine.ps1
.\.venv\Scripts\python.exe .\simple_airplay.py
```

`setup-engine.ps1` 从第三方项目的 GitHub Release 下载固定版本接收引擎，校验 SHA-256 后解压到 `engine/`。约需下载 114 MB。引擎可执行文件和依赖不提交到本仓库。

启动后点击「开始接收」。iPad 从右上角下拉控制中心，选择 **屏幕镜像（两个重叠矩形）** → 选择控制器显示的名称。音乐播放区域的 AirPlay 入口可能只发送音频。

## 构建 Windows 程序

```powershell
powershell -NoProfile -File .\scripts\build.ps1
```

输出为 `dist/SimpleAirPlay/`。该目录中的控制器 EXE、`_internal/` 和 `engine/` 必须一起保留。首次构建会创建独立虚拟环境并安装构建依赖。用 `SimpleAirPlay.exe --start` 可在打开窗口后自动开始接收。

## 使用与限制

- 画质参数是发给发送设备的请求，实际视频分辨率和帧率由 iOS / iPadOS 协商决定，不保证 4K 或 60fps。
- 全屏不会裁切或拉伸 iPad 画面；显示器比例不同会留下黑边。Alt+Tab 可切回控制窗口停止接收。
- 修改画质、解码或全屏设置前先停止接收，修改后重新连接屏幕镜像。
- DRM 视频或限制镜像的 App 可能拒绝播放或显示黑屏；本项目不解除这些限制。
- 网络连接状态不代表视频已解码；设备也可能只连接音频。
- 当前简易控制器未提供 PIN 配对开关。请在可信局域网使用，并在用完后停止接收。
- 防火墙需允许 `engine/uxplay-windows.exe` 在使用的网络上入站；客用 Wi-Fi / AP 隔离或 VPN 可能影响发现。
- 程序是实验性工具，目前只做过有限的 Windows 11 / iPad 实机验证。

## 本地数据

偏好设置和诊断日志位于 `%LOCALAPPDATA%\SimpleAirPlay`。日志可能包含设备标识、IP 或播放信息，提交问题前请先脱敏，不要直接上传整个目录。

引擎参数文件为 `%APPDATA%\leapbtw\uxplay-windows\arguments.txt`。显示偏好位于 `HKCU\Software\leapbtw\uxplay-windows`。控制器会备份自己修改的值，在停止时恢复；异常退出后，在下一次正常启动接收时尝试恢复。不要同时用其他软件修改同一引擎设置。

## 开源与第三方组件

控制器源码以 [MIT](LICENSE) 发布。AirPlay 引擎和运行库是独立的第三方组件，**不属于本项目 MIT 许可范围**。

- [UxPlay](https://github.com/FDH2/UxPlay)：AirPlay 接收引擎。
- [uxplay-windows 2.0.0.1736](https://github.com/leapbtw/uxplay-windows/tree/2.0.0.1736)：使用的 Windows 构建。
- 第三方二进制和许可由下载脚本原样保留，详见 [THIRD_PARTY.md](THIRD_PARTY.md)。

这是非官方兼容工具，与 Apple 无关联。AirPlay 等商标属于各自所有者。

## 贡献

欢迎通过 Issue 或 Pull Request 提交问题和改进。请注明 Windows / iPadOS 版本、网络连接方式、画质设置及复现步骤。提交日志前移除个人信息。建议优先改进连接状态识别、进程退出恢复、配置隔离和跨设备兼容性。