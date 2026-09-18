"""SimpleAirPlay: Chinese Windows controller for the bundled UxPlay receiver."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import winreg
import tkinter as tk
from tkinter import ttk, messagebox
import psutil

BASE = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
ENGINE = BASE / 'engine' / 'uxplay-windows.exe'
STATE = Path(os.environ['LOCALAPPDATA']) / 'SimpleAirPlay'
CONFIG = Path(os.environ['APPDATA']) / 'leapbtw' / 'uxplay-windows' / 'arguments.txt'
BACKUP = STATE / 'arguments.backup.json'
REG_BACKUP = STATE / 'display.backup.json'
REG_PATH = r'Software\leapbtw\uxplay-windows'
QUALITIES = {'流畅 · 720p': '1280x720@30', '清晰 · 1080p': '1920x1080@60',
             '超清 · 1440p': '2560x1440@60', '高分辨率 · 4K': '3840x2160@30'}


def set_display(fullscreen):
    previous = {}
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as key:
        for name in ('force_fs_enabled', 'renderer_mode'):
            try:
                value, kind = winreg.QueryValueEx(key, name)
                previous[name] = [value, kind]
            except FileNotFoundError:
                previous[name] = None
        REG_BACKUP.write_text(json.dumps(previous), encoding='utf-8')
        winreg.SetValueEx(key, 'force_fs_enabled', 0, winreg.REG_SZ, 'true' if fullscreen else 'false')
        winreg.SetValueEx(key, 'renderer_mode', 0, winreg.REG_SZ, 'd3d11')


def restore_display():
    if REG_BACKUP.exists():
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as key:
            for name, previous in json.loads(REG_BACKUP.read_text(encoding='utf-8')).items():
                if previous is None:
                    try:
                        winreg.DeleteValue(key, name)
                    except FileNotFoundError:
                        pass
                else:
                    winreg.SetValueEx(key, name, 0, previous[1], previous[0])
        REG_BACKUP.unlink()


def arguments(name, quality, compatible=False):
    if not re.fullmatch(r'[\w\-\u4e00-\u9fff]{1,40}', name):
        raise ValueError('名称限 1–40 个汉字、字母、数字、下划线或短横线，不含空格。')
    resolution = QUALITIES[quality]
    fps = resolution.split('@')[1]
    return f'-n {name} -nh -s {resolution} -fps {fps} -p 7000' + (' -avdec' if compatible else '')


def restore_config():
    restore_display()
    if BACKUP.exists():
        previous = json.loads(BACKUP.read_text(encoding='utf-8'))
        if previous['exists']:
            CONFIG.write_bytes(bytes.fromhex(previous['data']))
        else:
            CONFIG.unlink(missing_ok=True)
        BACKUP.unlink()


class App:
    def __init__(self, root):
        self.root, self.proc, self.log = root, None, None
        STATE.mkdir(parents=True, exist_ok=True)
        root.title('轻投屏 · SimpleAirPlay')
        root.geometry('700x670')
        root.minsize(700, 670)
        root.configure(bg='#f4f6fa')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f4f6fa')
        style.configure('TLabel', background='#f4f6fa', font=('Microsoft YaHei UI', 10))
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 24, 'bold'))
        style.configure('TButton', font=('Microsoft YaHei UI', 10), padding=10)
        frame = ttk.Frame(root, padding=30)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='把小屏幕，放到电脑上。', style='Title.TLabel').pack(anchor='w')
        ttk.Label(frame, text='iPhone / iPad → Windows 11  ·  AirPlay 无线投屏').pack(anchor='w', pady=(8, 23))
        self.status = tk.StringVar(value='● 尚未启动')
        ttk.Label(frame, textvariable=self.status, foreground='#245cbd').pack(anchor='w', pady=(0, 16))
        options = ttk.Frame(frame)
        options.pack(fill='x')
        ttk.Label(options, text='设备名称').grid(row=0, column=0, sticky='w')
        self.name = tk.StringVar(value='Windows-' + re.sub(r'[^\w-]', '', socket.gethostname())[:20])
        self.quality = tk.StringVar(value='超清 · 1440p')
        self.compatible = tk.BooleanVar(value=False)
        self.fullscreen = tk.BooleanVar(value=True)
        try:
            saved = json.loads((STATE / 'settings.json').read_text(encoding='utf-8'))
            self.name.set(saved['name'])
            if saved.get('version') == 2:
                if saved.get('quality') in QUALITIES:
                    self.quality.set(saved['quality'])
                self.compatible.set(saved.get('compatible', False))
                self.fullscreen.set(saved.get('fullscreen', True))
        except (OSError, ValueError, KeyError):
            pass
        self.entry = ttk.Entry(options, textvariable=self.name, font=('Microsoft YaHei UI', 11), width=30)
        self.entry.grid(row=1, column=0, sticky='ew', pady=(7, 0), padx=(0, 15))
        ttk.Label(options, text='画面质量').grid(row=0, column=1, sticky='w')
        self.combo = ttk.Combobox(options, textvariable=self.quality, values=list(QUALITIES), state='readonly', width=19)
        self.combo.grid(row=1, column=1, pady=(7, 0))
        self.compat_box = ttk.Checkbutton(frame, text='兼容模式：使用软件解码（黑屏时建议开启）', variable=self.compatible)
        self.compat_box.pack(anchor='w', pady=(15, 0))
        self.fullscreen_box = ttk.Checkbutton(frame, text='连接后全屏显示（保留原始比例，不裁切）', variable=self.fullscreen)
        self.fullscreen_box.pack(anchor='w', pady=(10, 0))
        ttk.Label(frame, text='1440p / 1080p 请求 60 帧；实际清晰度和帧率由 iPad 协商决定。', foreground='#666666').pack(anchor='w', pady=(10, 0))
        buttons = ttk.Frame(frame)
        buttons.pack(fill='x', pady=22)
        self.start_button = ttk.Button(buttons, text='开始接收', command=self.start)
        self.start_button.pack(side='left', expand=True, fill='x', padx=(0, 10))
        self.stop_button = ttk.Button(buttons, text='停止接收', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', expand=True, fill='x')
        ttk.Separator(frame).pack(fill='x', pady=(0, 20))
        ttk.Label(frame, text='1  手机 / iPad 与电脑连接同一路由器 / Wi-Fi\n\n2  点击「开始接收」\n\n3  控制中心 → 屏幕镜像（两个重叠矩形）→ 选择设备', wraplength=620).pack(anchor='w')
        ttk.Label(frame, text='全屏时可 Alt+Tab 切回此窗口停止接收；更改画质后需重新连接。', foreground='#666666').pack(anchor='w', pady=(15, 8))
        footer = ttk.Frame(frame)
        footer.pack(fill='x', side='bottom')
        ttk.Button(footer, text='连接帮助', command=self.help).pack(side='left')
        ttk.Button(footer, text='查看日志', command=lambda: os.startfile(str(STATE))).pack(side='right')
        root.protocol('WM_DELETE_WINDOW', self.close)
        self.started = 0
        root.after(1000, self.poll)

    def start(self):
        if self.proc is not None:
            return
        owns_config = False
        try:
            args = arguments(self.name.get().strip(), self.quality.get(), self.compatible.get())
            if not ENGINE.is_file():
                raise RuntimeError('缺少 engine 文件夹，请完整解压程序。')
            for process in psutil.process_iter(['name']):
                if process.info['name'] == 'uxplay-windows.exe':
                    raise RuntimeError('已有 UxPlay 接收程序在运行。请先从任务栏托盘退出它，再启动。')
            restore_config()
            owns_config = True
            BACKUP.write_text(json.dumps({'exists': CONFIG.exists(), 'data': CONFIG.read_bytes().hex() if CONFIG.exists() else ''}), encoding='utf-8')
            CONFIG.parent.mkdir(parents=True, exist_ok=True)
            CONFIG.write_text(args, encoding='utf-8')
            set_display(self.fullscreen.get())
            (STATE / 'settings.json').write_text(json.dumps({'version': 2, 'name': self.name.get(), 'quality': self.quality.get(), 'compatible': self.compatible.get(), 'fullscreen': self.fullscreen.get()}, ensure_ascii=False), encoding='utf-8')
            stamp = time.strftime('%Y%m%d-%H%M%S')
            self.log = (STATE / f'receiver-{stamp}.log').open('w', encoding='utf-8')
            self.log.write(f'Arguments: {args}\nRenderer: d3d11; fullscreen: {self.fullscreen.get()}\nVideo diagnostics: video-{stamp}.log\n')
            self.log.flush()
            env = os.environ.copy()
            env['GST_DEBUG'] = '3'
            env['GST_DEBUG_NO_COLOR'] = '1'
            env['GST_DEBUG_FILE'] = str(STATE / f'video-{stamp}.log')
            self.proc = subprocess.Popen([str(ENGINE)], cwd=ENGINE.parent, env=env, stdout=self.log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            self.started = time.monotonic()
            self.status.set('● 正在启动接收引擎…')
            self.start_button.configure(state='disabled')
            self.stop_button.configure(state='normal')
            self.entry.configure(state='disabled')
            self.combo.configure(state='disabled')
            self.compat_box.configure(state='disabled')
            self.fullscreen_box.configure(state='disabled')
        except Exception as error:
            if self.proc is None:
                if self.log:
                    self.log.close()
                    self.log = None
                if owns_config:
                    restore_config()
            messagebox.showerror('启动失败', str(error))

    def poll(self):
        if self.proc:
            if self.proc.poll() is not None:
                code = self.proc.returncode
                self.stop()
                self.status.set(f'● 接收引擎已退出（{code}），请查看日志或连接帮助')
            else:
                try:
                    listeners = psutil.Process(self.proc.pid).net_connections(kind='tcp')
                    ready = any(c.status == psutil.CONN_LISTEN for c in listeners)
                    connected = any(c.status == psutil.CONN_ESTABLISHED and c.raddr and c.raddr.ip not in ('127.0.0.1', '::1') for c in listeners)
                    if connected:
                        self.status.set('● 设备已建立网络连接 · 画面取决于 iPad 是否开启屏幕镜像')
                    elif ready:
                        self.status.set('● 接收端口已就绪 · 请在手机上选择 ' + self.name.get())
                    elif time.monotonic() - self.started > 15:
                        self.status.set('● 引擎运行中，尚未检测到接收端口 · 请查看连接帮助')
                except (psutil.Error, OSError):
                    self.status.set('● 引擎运行中 · 请在手机上检查屏幕镜像列表')
        self.root.after(1500, self.poll)

    def stop(self):
        if self.proc:
            try:
                parent = psutil.Process(self.proc.pid)
                children = parent.children(recursive=True)
                parent.terminate()
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass
                psutil.wait_procs([parent] + children, timeout=2)
            except psutil.NoSuchProcess:
                pass
            self.proc = None
        if self.log:
            self.log.close()
            self.log = None
        restore_config()
        self.status.set('● 已停止接收')
        self.start_button.configure(state='normal')
        self.stop_button.configure(state='disabled')
        self.entry.configure(state='normal')
        self.combo.configure(state='readonly')
        self.compat_box.configure(state='normal')
        self.fullscreen_box.configure(state='normal')

    def help(self):
        messagebox.showinfo('连接帮助', '• 手机和电脑须在同一局域网；电脑可连接网线。\n• 若 Windows 弹出防火墙提示，请允许专用网络访问。\n• 客用 Wi-Fi / AP 隔离会阻止设备互相发现。\n• 若 VPN 影响局域网发现，可暂时断开后重试。\n• Bonjour Service 应处于运行状态。\n• 停止后再开始，可重新建立接收服务。\n\n关闭本窗口会停止接收。受保护视频可能无法镜像。\n这是基于 UxPlay 的非官方兼容接收器，实际兼容性需用你的 iOS 设备确认。')

    def close(self):
        self.stop()
        self.root.destroy()


if __name__ == '__main__':
    import ctypes
    ctypes.windll.kernel32.CreateMutexW.restype = ctypes.c_void_p
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, 'Local\\SimpleAirPlay.Controller')
    if ctypes.windll.kernel32.GetLastError() == 183:
        sys.exit(0)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except OSError:
        pass
    root = tk.Tk()
    app = App(root)
    if '--start' in sys.argv:
        root.after(300, app.start)
    root.mainloop()
