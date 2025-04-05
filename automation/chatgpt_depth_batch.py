#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script automates interactions with the ChatGPT application on macOS:
1. Checks or launches the ChatGPT app.
2. Creates new chats.
3. Sends an image and a text prompt to ChatGPT.
4. Captures ChatGPT responses (text and optionally images).
5. Stores results locally.

Requires: 
- pyautogui
- Pillow (for ImageGrab)
- macOS environment with AppleScript support
"""

import os
import json
import time
import subprocess
import random

import pyautogui
from PIL import ImageGrab

CONFIG_FILE = "chatgpt_config.json"

DEFAULT_CONFIG = {
    "response_timeout": 120,
    "output_dir": "./data/example/chatgpt_results",
    "save_results": True,
    "default_prompts_file": "./prompts/grayscale_depth.txt",
    "num_images_to_process": 100  
}


def load_config():
    """
    Load configuration from CONFIG_FILE if it exists. Otherwise, create a new
    default configuration file and return the default configuration dictionary.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as exc:
            print(f"Unable to read config file. Using default config: {exc}")
            return DEFAULT_CONFIG
    else:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG


def save_config(config):
    """
    Save the given configuration dictionary as JSON to CONFIG_FILE.
    """
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            json.dump(config, file, ensure_ascii=False, indent=2)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as exc:
        print(f"Unable to save config file: {exc}")


def run_applescript(script):
    """
    Run the given AppleScript string.
    Returns a tuple of (stdout, returncode).
    If an error occurs, return (None, -1).
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
    except Exception as exc:
        print(f"Error running AppleScript: {exc}")
        return (None, -1)


def check_chatgpt_running():
    """
    Check if the ChatGPT application is running.
    If not, attempt to launch it.
    Return True if ChatGPT is running or successfully launched, False otherwise.
    """
    try:
        script = '''
            tell application "System Events"
                return application process "ChatGPT" exists
            end tell
        '''
        is_running, _ = run_applescript(script)
        if is_running != "true":
            print("ChatGPT is not running. Attempting to launch...")
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
            print("ChatGPT launched.")
        return True
    except Exception as exc:
        print(f"Error checking ChatGPT status: {exc}")
        return False


def create_new_chat():
    """
    Attempt to create a new ChatGPT conversation window.
    If successful, return True; otherwise, return False.
    Note: This may fail if the ChatGPT application does not support
    this keyboard shortcut or flow.
    """
    if not check_chatgpt_running():
        print("Unable to access ChatGPT.")
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
        print("--- New Chat Created ---")
        return True
    else:
        print("Failed to create new chat.")
        return False


def ask_chatgpt_with_image(img_path, prompt, config):
    """
    Send an image and text prompt to ChatGPT using AppleScript automation.
    1. Copy the text prompt to the clipboard and paste into ChatGPT.
    2. Copy the image file to the clipboard and paste into ChatGPT.
    3. Press Enter and attempt to retrieve the latest response text.
    4. Return the retrieved response text or a timeout message if it fails.
    """
    if not check_chatgpt_running():
        raise Exception("ChatGPT is not running or cannot be accessed.")

    shell_safe_img_path = img_path.replace('"', '\\"')
    # Escape double quotes and convert line breaks for AppleScript
    safe_prompt = prompt.replace('"', '\\"').replace('\n', '\\n')

    applescript_cmd = f'''
        -- Step 1: Copy prompt to the system clipboard
        do shell script "osascript -e 'set the clipboard to \\"{safe_prompt}\\"'"
        delay 0.5

        -- Step 2: Activate ChatGPT and paste text
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

        -- Step 3: Copy the image file to the system clipboard
        do shell script "osascript -e 'set the clipboard to (POSIX file \\"{shell_safe_img_path}\\")'"
        delay 2

        -- Step 4: Paste the image into ChatGPT
        tell application "System Events"
            tell application process "ChatGPT"
                keystroke "v" using {{command down}}
                delay 5
            end tell
        end tell

        -- Step 5: Press Enter to send
        tell application "System Events"
            tell application process "ChatGPT"
                key code 36
                delay 120

                -- Step 6: Attempt to retrieve the latest response
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

    start_time = time.time()
    response = None
    timeout = config.get("response_timeout", 130)

    while response is None and (time.time() - start_time) < timeout:
        result, status = run_applescript(applescript_cmd)
        if status == 0:
            response = result
        else:
            time.sleep(2)

    if response is None:
        response = f"Response timed out after waiting {timeout} seconds."

    return response


def copy_image_from_screen(x, y, x_shift=20, y_shift=0):
    """
    Automate the mouse/keyboard to copy an image from the screen via context menu.
    1. Move the mouse to (x, y).
    2. Right-click to open context menu.
    3. Move to (x + x_shift, y + y_shift).
    4. Click to select 'Copy Image'.
    """
    time.sleep(2)
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.rightClick()
    time.sleep(0.5)
    pyautogui.moveTo(x + x_shift, y + y_shift, duration=0.2)
    pyautogui.click()


def copy_gpt_output_image_via_pyautogui(x, y, x_shift, y_shift, img_name, output_dir):
    """
    Use PyAutoGUI and PIL to capture GPT output images from screen to clipboard.
    1. Invokes `copy_image_from_screen` to right-click and copy the image.
    2. Grabs the clipboard content using ImageGrab.grabclipboard().
    3. Saves the image as 'depth_map.png' within '{output_dir}/{img_name}'.
    """
    print(f"Attempting to copy GPT output image at coordinates ({x}, {y})...")
    copy_image_from_screen(x, y, x_shift, y_shift)

    # Wait for clipboard to update
    time.sleep(2)

    image = ImageGrab.grabclipboard()
    if image is None:
        print("No image object found in the clipboard.")
        return

    target_folder = os.path.join(output_dir, img_name)
    os.makedirs(target_folder, exist_ok=True)
    target_path = os.path.join(target_folder, "depth_map.png")

    try:
        image.save(target_path, "PNG")
        print(f"Image saved: {target_path}")
    except Exception as exc:
        print(f"Failed to save image: {exc}")


def main():
    """
    Main workflow:
    1. Load configuration.
    2. Read default prompt from file.
    3. Prompt the user for an image folder path.
    4. Ensure ChatGPT is running.
    5. For each image in that folder:
       a) (Optional) Create a new chat.
       b) Send image & prompt to ChatGPT and capture response.
       c) Save text response as 'output.txt'.
       d) Attempt to capture any GPT-returned image via PyAutoGUI, saving as 'depth_map.png'.
       
    修改内容：支持从输入的图片数据集中随机选择指定数量（默认为100）的图片进行处理，而非处理所有图片。
    """
    config = load_config()
    output_dir = config["output_dir"]
    os.makedirs(output_dir, exist_ok=True)

    # Read the default prompt
    prompts_file = config["default_prompts_file"]
    if not os.path.exists(prompts_file):
        print(f"Default prompts file does not exist: {prompts_file}")
        return

    with open(prompts_file, 'r', encoding='utf-8') as file:
        default_prompt = file.read().strip()

    if not default_prompt:
        print("Prompt file is empty. Please check.")
        return

    # Ask user for the image folder path
    image_folder = input("Please enter the folder path containing images: ").strip()
    if not os.path.isdir(image_folder):
        print(f"Invalid folder: {image_folder}")
        return

    # Ensure ChatGPT is running
    if not check_chatgpt_running():
        print("Unable to launch or access ChatGPT. Exiting.")
        return

    # Collect image files
    valid_exts = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]
    images = sorted([
        f for f in os.listdir(image_folder)
        if not f.startswith('.') and os.path.splitext(f)[1].lower() in valid_exts
    ])

    if not images:
        print("No valid images found in the specified folder.")
        return

    total_images = len(images)
    print(f"\nFound {total_images} images in folder: {image_folder}.\n")

    default_num = config.get("num_images_to_process", 100)
    if total_images > default_num:
        user_input = input(f"Enter the number of images to process (default {default_num}, type 'all' for all images): ").strip()
        if user_input.lower() == "all":
            num_to_process = total_images
        elif user_input == "":
            num_to_process = default_num
        else:
            try:
                num_to_process = int(user_input)
            except:
                print(f"Invalid input. Using default {default_num} images.")
                num_to_process = default_num

        if num_to_process < total_images:
            images = random.sample(images, num_to_process)
            images.sort()  
    else:
        num_to_process = total_images

    print(f"Processing {len(images)} images.\n")

    for idx, img_name in enumerate(images, start=1):
        print(f"[{idx}/{len(images)}] Processing image: {img_name}")
        img_path = os.path.join(image_folder, img_name)
        base_name, _ = os.path.splitext(img_name)

        # (Optional) Create a new chat for each image
        created = create_new_chat()
        if not created:
            print("Failed to create a new chat, sending in the current chat window...")

        # Send the image and prompt to ChatGPT
        try:
            response = ask_chatgpt_with_image(img_path, default_prompt, config)
        except Exception as exc:
            response = f"Exception occurred for {img_name}: {str(exc)}"

        # Save text response
        save_folder = os.path.join(output_dir, base_name)
        os.makedirs(save_folder, exist_ok=True)
        result_file = os.path.join(save_folder, "output.txt")
        with open(result_file, 'w', encoding='utf-8') as rf:
            rf.write(response)
        print(f"Text result saved to: {result_file}\n")

        # Attempt to capture GPT output image
        # Adjust coordinates (x, y, x_shift, y_shift) to match actual ChatGPT UI
        copy_gpt_output_image_via_pyautogui(
            x=518,
            y=580,
            x_shift=30,
            y_shift=0,
            img_name=base_name,
            output_dir=output_dir
        )

        time.sleep(1)

    print("=== All images have been processed ===")


if __name__ == "__main__":
    main()