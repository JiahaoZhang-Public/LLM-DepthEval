#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import subprocess
from datetime import datetime

# 配置文件名
CONFIG_FILE = "chatgpt_config.json"

# 默认配置
DEFAULT_CONFIG = {
    # 等待 ChatGPT 响应的最长时间（秒）
    "response_timeout": 130,
    # 存放结果的目录
    "output_dir": "./chatgpt_results",
    # 是否保存结果
    "save_results": True,
    # 默认的提示词文件路径
    "default_prompts_file": "./prompts.txt"
}


def load_config():
    """
    尝试从 CONFIG_FILE 加载配置，如不存在则创建默认配置文件并返回默认配置。
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"无法读取配置文件，使用默认配置: {e}")
            return DEFAULT_CONFIG
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(config):
    """
    将配置以 JSON 格式写入到 CONFIG_FILE
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"已将配置保存到 {CONFIG_FILE}")
    except Exception as e:
        print(f"无法保存配置文件: {e}")


def run_applescript(script):
    """
    执行 AppleScript 脚本，返回 (stdout, returncode)
    """
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0 and result.stderr:
            print(f"AppleScript warning: {result.stderr}")
        return (result.stdout.strip(), result.returncode)
    except Exception as e:
        print(f"运行 AppleScript 出错: {e}")
        return (None, -1)


def check_chatgpt_running():
    """
    检查 ChatGPT 是否在运行，如果未运行则尝试启动。
    返回 True 表示已确保 ChatGPT 运行，False 表示失败。
    """
    try:
        script = '''
            tell application "System Events"
                return application process "ChatGPT" exists
            end tell
        '''
        is_running, _ = run_applescript(script)
        if is_running != "true":
            print("ChatGPT 未运行，正在尝试启动...")
            launch_script = '''
                tell application "ChatGPT" to activate
                delay 2
                tell application "System Events"
                    repeat 5 times
                        if application process "ChatGPT" exists then
                            exit repeat
                        end if
                        delay 1
                    end repeat
                end tell
            '''
            run_applescript(launch_script)
            print("ChatGPT 已启动。")
        return True
    except Exception as e:
        print(f"检查 ChatGPT 状态出错: {e}")
        return False


def create_new_chat():
    """
    新建 ChatGPT 对话窗口。
    如果成功则返回 True，否则返回 False。
    若 ChatGPT 不支持此功能，可能会失败。
    """
    if not check_chatgpt_running():
        print("无法访问 ChatGPT。")
        return False

    script = '''
        tell application "ChatGPT"
            activate
            delay 1
        end tell

        tell application "System Events"
            tell process "ChatGPT"
                try
                    keystroke "n" using command down
                    delay 1
                    return true
                on error errMsg
                    return false
                end try
            end tell
        end tell
    '''
    result, status = run_applescript(script)
    if status == 0 and result == "true":
        print("--- 已新建对话 ---")
        return True
    else:
        print("新建对话失败。")
        return False


def ask_chatgpt_with_image(img_path, prompt, config):
    """
    通过 AppleScript 将img_path对应的图片文件复制到剪贴板，
    然后在ChatGPT中粘贴图片，再粘贴提示词发送，最后获取回复文本。
    """
    if not check_chatgpt_running():
        raise Exception("ChatGPT 未启动或无法访问。")

    # 将图片路径做简单转义（如有引号）：
    shell_safe_img_path = img_path.replace('"', '\\"')
    # 将提示词做简单转义（多行换行符 \n -> \\n，双引号 -> \\"）：
    safe_prompt = prompt.replace('"', '\\"').replace('\n', '\\n')

    # AppleScript：
    # Step 1: 复制文本 -> Step 2: ChatGPT粘贴文本 -> Step 3: 复制图片 -> Step 4: ChatGPT粘贴图片 -> Step 5: 回车 -> Step 6: 取最新回复
    applescript = f'''
        -- Step 1: 将提示词写入系统剪贴板
        do shell script "osascript -e 'set the clipboard to \\"{safe_prompt}\\"'"
        delay 0.5

        -- Step 2: 激活 ChatGPT 并粘贴文本
        tell application "ChatGPT" to activate
        delay 1

        tell application "System Events"
            tell application process "ChatGPT"
                set frontmost to true
                delay 0.5

                keystroke "v" using {{command down}}
                delay 1
            end tell
        end tell

        -- Step 3: 将图片文件复制到系统剪贴板 (POSIX file)
        do shell script "osascript -e 'set the clipboard to (POSIX file \\"{shell_safe_img_path}\\")'"
        delay 2

        -- Step 4: 在 ChatGPT 粘贴图片
        tell application "System Events"
            tell application process "ChatGPT"
                keystroke "v" using {{command down}}
                delay 5
                  -- 等待图片上传
            end tell
        end tell

        -- Step 5: 回车发送
        tell application "System Events"
            tell application process "ChatGPT"
                key code 36
                delay 120

                -- Step 6: 尝试获取最新回答
                set responseText to ""
                try
                    set responseText to value of text area 2 of group 1 of group 1 of window 1
                on error errMsg
                    set responseText to "Failed to get ChatGPT response: " & errMsg
                end try
                return responseText
            end tell
        end tell
    '''

    # 轮询直到拿到结果或超时
    start_time = time.time()
    response = None
    timeout = config.get("response_timeout", 130)

    while response is None and (time.time() - start_time) < timeout:
        result, status = run_applescript(applescript)
        if status == 0:  # 说明 AppleScript 成功执行
            response = result
        else:
            time.sleep(2)

    if response is None:
        response = f"等待响应超时，已等待 {timeout} 秒。"

    return response


def main():
    """
    主流程：
    1. 加载配置
    2. 从 default_prompts_file 读取提示词
    3. 询问图片文件夹
    4. 对文件夹中的所有图片，逐张粘贴图片 & 粘贴提示词
    5. 保存结果到 {output_dir}/{图片名}/output.txt
    """
    config = load_config()
    output_dir = config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    # 读取默认提示词
    prompts_file = config["default_prompts_file"]
    if not os.path.exists(prompts_file):
        print(f"默认提示词文件不存在: {prompts_file}")
        return

    with open(prompts_file, 'r', encoding='utf-8') as f:
        default_prompt = f.read().strip()

    if not default_prompt:
        print("提示词文件内容为空，请检查。")
        return

    # 让用户输入图片文件夹路径
    image_folder = input("请输入包含图片的文件夹路径：").strip()
    if not os.path.isdir(image_folder):
        print(f"无效的文件夹：{image_folder}")
        return

    # 确保 ChatGPT 已运行
    if not check_chatgpt_running():
        print("无法启动或访问 ChatGPT，脚本退出。")
        return

    # 收集文件夹中的图片
    valid_exts = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
    images = sorted([
        f for f in os.listdir(image_folder)
        if not f.startswith('.') and os.path.splitext(f)[1].lower() in valid_exts
    ])

    if not images:
        print("指定文件夹中没有找到图片文件。")
        return

    print(f"\n开始处理文件夹：{image_folder}，共 {len(images)} 张图片。\n")

    # 遍历图片
    for idx, img_name in enumerate(images, start=1):
        print(f"[{idx}/{len(images)}] 处理图片：{img_name}")
        img_path = os.path.join(image_folder, img_name)
        base_name, _ = os.path.splitext(img_name)

        # 可选：每张图片都新建对话（若不想每张都新建，可以注释掉）
        created = create_new_chat()
        if not created:
            print("新建对话失败，尝试直接在当前对话发送。")

        # 调用我们的函数：复制图片 -> 粘贴 -> 复制提示词 -> 粘贴 -> 等待回复
        try:
            response = ask_chatgpt_with_image(img_path, default_prompt, config)
        except Exception as e:
            response = f"处理图片 {img_name} 时出现异常：{str(e)}"

        # 保存结果
        save_folder = os.path.join(output_dir, base_name)
        os.makedirs(save_folder, exist_ok=True)
        result_file = os.path.join(save_folder, "output.txt")

        with open(result_file, 'w', encoding='utf-8') as rf:
            rf.write(response)

        print(f"结果已保存至：{result_file}\n")
        time.sleep(1)  # 略作停顿，避免切换过快

    print("=== 所有图片处理完成 ===")


if __name__ == "__main__":
    main()