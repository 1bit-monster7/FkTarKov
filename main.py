import sys
import time
import os
import keyboard
import pyautogui
import pygame
from PIL import ImageGrab
import tkinter as tk
import random
import string
import win32gui
import win32con
import configparser

# Initialize pygame mixer
pygame.mixer.init()

if getattr(sys, 'frozen', False):
    # 如果是打包后的环境，获取 exe 文件的目录
    current_dir = os.path.dirname(sys.executable)
else:
    # 如果是开发环境，获取脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))

assets_dir = os.path.join(current_dir, 'assets')
sounds_dir = os.path.join(current_dir, 'sounds')

# 创建目录（如果不存在）
if not os.path.exists(assets_dir):
    os.makedirs(assets_dir)
if not os.path.exists(sounds_dir):
    os.makedirs(sounds_dir)


def update_image_paths():
    return [os.path.join(assets_dir, f) for f in os.listdir(assets_dir) if
            f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))]


def get_xywh(x, y, x2, y2):
    return x, y, x2 - x, y2 - y


def play_sound(file_name):
    sound_path = os.path.join(sounds_dir, file_name)
    pygame.mixer.music.load(sound_path)
    pygame.mixer.music.play()


def on_shift_f1_press(event):
    if keyboard.is_pressed('shift'):
        global target_x, target_y
        # 获取当前鼠标位置
        target_x, target_y = pyautogui.position()
        print(f"Shift+F1 按下，获取当前鼠标位置: {target_x}, {target_y}")
        play_sound('coordinate_recorded.mp3')


def on_shift_f2_press(event):
    if keyboard.is_pressed('shift'):
        global isRun, image_paths
        # 切换循环状态
        isRun = not isRun
        state = "开启" if isRun else "关闭"
        image_paths = update_image_paths()
        print(f"Shift+F2 按下，循环状态: {state}")
        if isRun:
            play_sound('toggle_open.mp3')
        else:
            play_sound('toggle_close.mp3')


def on_f3_press(event):
    if keyboard.is_pressed('f3'):
        take_screenshot()


def on_f4_press(event):
    if keyboard.is_pressed('f4'):
        take_screenshot_and_save()

class ScreenshotApp:
    def __init__(self):
        self.root = tk.Tk()
        self.winHwnd = self.root.winfo_id()
        self.set_window_on_top()
        self.root.attributes("-alpha", 0.3)
        self.root.configure(background='black')
        self.root.lift()
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='black')
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.screenshot_region = None
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def set_window_on_top(self):
        self.root.attributes("-fullscreen", True)
        # 激活窗口并将其带到前台
        win32gui.SetForegroundWindow(self.winHwnd)
        win32gui.SetWindowPos(self.winHwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red',width=3)

    def on_mouse_drag(self, event):
        curX, curY = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, curX, curY)

    def on_button_release(self, event):
        end_x, end_y = (event.x, event.y)
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)

        # 确保宽度和高度大于零
        if width > 0 and height > 0:
            self.screenshot_region = (left, top, left + width, top + height)
        else:
            self.screenshot_region = None

        self.root.destroy()  # 立即关闭窗口


def take_screenshot():
    app = ScreenshotApp()
    app.root.mainloop()

    if app.screenshot_region:
        global region
        region = app.screenshot_region
        print(f"截图区域更新为: {region} 同时更新ini配置文件")
        # 更新配置文件中的 region 设置
        save_settings_to_ini(config_file, region, pyautogui.PAUSE)
    else:
        print("选择的区域无效，请重试。")


def take_screenshot_and_save():
    app = ScreenshotApp()
    app.root.mainloop()
    if app.screenshot_region:
        screenshot = ImageGrab.grab(bbox=app.screenshot_region)
        # 生成随机文件名
        file_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10)) + '.png'
        file_path = os.path.join(assets_dir, file_name)
        screenshot.save(file_path)
        print(f"截图保存到: {file_path}")
    else:
        print("选择的区域无效，请重试。")


# 读取配置设置
def read_settings_from_ini(config_file):
    if not os.path.isfile(config_file):
        print("配置文件不存在，开始创建默认配置...")
        create_default_config()

    config = configparser.ConfigParser()
    config.read(config_file)
    settings = {}

    if 'settings' in config:
        try:
            # 读取 region 设置
            x = int(config.get('settings', 'x', fallback='0'))
            y = int(config.get('settings', 'y', fallback='0'))
            width = int(config.get('settings', 'width', fallback=str(screen_width)))
            height = int(config.get('settings', 'height', fallback=str(screen_height)))
            settings['region'] = (x, y, width, height)

            # 读取 PAUSE 设置
            pause = float(config.get('settings', 'pause', fallback='0.04'))
            settings['pause'] = pause

            return settings
        except ValueError:
            print("从 ini 文件读取设置失败，使用默认值。")

    # 如果配置读取失败，返回默认设置
    return {
        'region': (0, 0, screen_width, screen_height),
        'pause': 0.04
    }


# 保存配置设置到 ini 文件
def save_settings_to_ini(config_file, region, pause):
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    config = configparser.ConfigParser()
    config['settings'] = {
        'x': region[0],
        'y': region[1],
        'width': region[2],
        'height': region[3],
        'pause': pause
    }

    with open(config_file, 'w') as configfile:
        config.write(configfile)
    print("配置已保存到 ini 文件中。")


# 创建默认配置并保存到 ini 文件
def create_default_config():
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    default_settings = {
        'x': 0,
        'y': 0,
        'width': screen_width,
        'height': screen_height,
        'pause': 0.04
    }

    config = configparser.ConfigParser()
    config['settings'] = default_settings

    with open(config_file, 'w') as configfile:
        config.write(configfile)
    print("默认配置已创建并保存到 ini 文件中。")


# 注册按键事件
keyboard.on_press_key("f1", on_shift_f1_press)
keyboard.on_press_key("f2", on_shift_f2_press)
keyboard.on_press_key("f3", on_f3_press)
keyboard.on_press_key("f4", on_f4_press)
# 指定区域的坐标和大小
# 初始化 image_paths
image_paths = update_image_paths()
if not image_paths:
    print(f"当前assets目录下，暂无任何图像文件: {assets_dir}")

# 获取屏幕宽度和高度
screen_width, screen_height = pyautogui.size()
print(f"屏幕分辨率: {screen_width} x {screen_height}")

# 检查 config 目录是否存在
config_dir = 'config'
config_file = os.path.join(config_dir, 'settings.ini')

# isRun 控制开关
isRun = False
# 截图区域
# 读取当前设置
settings = read_settings_from_ini(config_file)
region = settings['region']
pyautogui.PAUSE = settings['pause']  # 设置 PAUSE
# 指定的容器位置
target_x = 0
target_y = 0

# 检查 config 目录是否存在
config_dir = 'config'
config_file = os.path.join(config_dir, 'settings.ini')

print(f"当前默认查找区域: {region}")
print(f"图像文件路径列表: {image_paths}")
print('程序初始化完毕！')
print("shift+F1 指定需要存放的容器位置")
print("shift+F2 开始 or 暂停 识别")
print("F3 指定截图区域 并将范围信息存储至本地 之后启动无需再次设置")
print("F4 程序自带的截图功能 框选需要截图的内容，即自动添加至运行目录下的 assets目录")

# 无限循环
while True:
    if isRun:
        found = False
        for image_path in image_paths:
            try:
                start_time = time.time()  # 记录开始时间

                # 在指定区域内查找图像
                location = pyautogui.locateCenterOnScreen(image_path, region=region, confidence=0.9)
                if location:
                    img_x, img_y = location
                    print(f"图像找到: {image_path}，位置: {img_x}, {img_y}")

                    # 移动鼠标到找到的图像位置
                    pyautogui.moveTo(img_x, img_y)

                    # 按住鼠标左键
                    pyautogui.mouseDown()

                    # 拖动鼠标到目标位置
                    pyautogui.moveTo(target_x, target_y)  # 可选：增加duration参数使拖动更加平滑

                    # 释放鼠标左键
                    pyautogui.mouseUp()

                    # 记录结束时间并计算耗时
                    end_time = time.time()
                    duration = end_time - start_time

                    # 打印操作完成信息
                    print(f"拖动到目标位置: {target_x}, {target_y}")
                    print(f"操作耗时: {duration * 1000:.4f}毫秒")
                    found = True
                    break
                else:
                    print(f"图像未找到: {image_path}")
            except pyautogui.ImageNotFoundException:
                pass
            except Exception as e:
                print(f"发生错误: {e}")
        if not found:
            print("所有图像均未找到")
    time.sleep(0.001)
