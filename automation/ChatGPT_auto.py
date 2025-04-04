#!/usr/bin/env python3
import os
import json
import time
import subprocess
from datetime import datetime

# Configuration file path
CONFIG_FILE = "chatgpt_config.json"

# Default configuration
DEFAULT_CONFIG = {
    # Response wait timeout (seconds)
    "response_timeout": 130,  # 2 minutes 10 seconds
    # Interval between each prompt (seconds)
    "prompt_interval": 120,  # 2 minutes
    # Results save directory
    "output_dir": "./chatgpt_results",
    # Whether to save results
    "save_results": True, # NO SUPPORT DOWNLOAD IMAGE, ONLY SUPPORT RESPONSE TEXT
    # Whether to add a fixed prefix
    "add_prefix": True,
    # Fixed prefix text
    "prompt_prefix": "Please generate a picture based on the following prompts:\n\n",
    # How many prompts to send before creating a new chat
    "new_chat_after_prompts": 1,
    # Default prompts file path
    "default_prompts_file": "./prompts.txt"
}

# Sample prompts
SAMPLE_PROMPTS = [
    "a photo of a bench",
    "a photo of a cow",
    "a photo of a bicycle"
]


def load_config():
    """Load configuration file, create default config if it doesn't exist"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"Failed to load configuration file: {str(e)}, using default configuration")
        return DEFAULT_CONFIG


def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Failed to save configuration file: {str(e)}")


def create_sample_prompts_file(file_path):
    """Create a sample prompts file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else '.', exist_ok=True)
        
        # Write sample prompts
        with open(file_path, 'w', encoding='utf-8') as f:
            for prompt in SAMPLE_PROMPTS:
                f.write(prompt + '\n')
        
        print(f"Sample prompts file created: {file_path}")
        return True
    except Exception as e:
        print(f"Failed to create sample prompts file: {str(e)}")
        return False


def run_applescript(script):
    """Run AppleScript and return results"""
    try:
        result = subprocess.run(['osascript', '-e', script], 
                               capture_output=True, 
                               text=True, 
                               check=False)
        
        if result.returncode != 0 and result.stderr:
            print(f"AppleScript warning: {result.stderr}")
            
        return result.stdout.strip(), result.returncode
    except Exception as e:
        print(f"Error running AppleScript: {str(e)}")
        return None, -1


def check_chatgpt_running():
    """Check if ChatGPT app is running, try to start it if not"""
    try:
        script = '''
            tell application "System Events"
                return application process "ChatGPT" exists
            end tell
        '''
        
        is_running, _ = run_applescript(script)
        
        if is_running != "true":
            print("ChatGPT is not running, attempting to start...")
            
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
            print("ChatGPT has been launched")
            
        return True
    except Exception as e:
        print(f"Error checking ChatGPT status: {str(e)}")
        return False


def create_new_chat():
    """Create a new chat window"""
    if not check_chatgpt_running():
        print("Cannot access ChatGPT application")
        return False
        
    script = '''
        tell application "ChatGPT"
            activate
            delay 1
        end tell
        
        tell application "System Events"
            tell process "ChatGPT"
                try
                    -- Try using keyboard shortcut
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
    
    if status != 0 or result != "true":
        print("Failed to create new chat")
        return False
    
    print("---New chat created---")
    return True


def ask_chatgpt(prompt, config, timeout=None):
    """Send a question to ChatGPT and get the answer"""
    if timeout is None:
        timeout = config["response_timeout"]
        
    if not check_chatgpt_running():
        raise Exception("Cannot access ChatGPT application")
    
    # Add prefix if needed
    final_prompt = config["prompt_prefix"] + prompt if config["add_prefix"] else prompt
    # Handle special characters
    safe_prompt = final_prompt.replace('"', '\\"').replace('\n', '\\n')
    
    script = f'''
        tell application "ChatGPT"
            activate
            delay 1
            
            tell application "System Events"
                tell process "ChatGPT"
                    -- Input prompt
                    keystroke "{safe_prompt}"
                    delay 0.5
                    keystroke return
                    
                    -- Wait for response to start generating
                    delay 3
                    
                    -- Try to get response
                    set responseText to ""
                    try
                        -- Try to get latest message
                        set responseText to value of text area 2 of group 1 of group 1 of window 1
                    on error errMsg
                        set responseText to "Failed to get ChatGPT response: " & errMsg
                    end try
                    
                    return responseText
                end tell
            end tell
        end tell
    '''
    
    # Set timeout handling
    start_time = time.time()
    response = None
    
    while response is None and (time.time() - start_time) < timeout:
        result, status = run_applescript(script)
        
        if status == 0:
            response = result
        else:
            time.sleep(2)  # Brief wait before retry
    
    if response is None:
        return f"Response wait timeout, waited {timeout} seconds"
    
    return response


def batch_ask_questions(prompts, config):
    """Process batch questions"""
    if not isinstance(prompts, list) or len(prompts) == 0:
        print("No prompts provided")
        return
    
    print(f"\nStarting to process {len(prompts)} questions...")
    if config["add_prefix"]:
        print(f"All prompts will be prefixed with: \"{config['prompt_prefix'][:30]}...\"")
    
    # Create results directory (if it doesn't exist and saving is enabled)
    if config["save_results"]:
        try:
            os.makedirs(config["output_dir"], exist_ok=True)
        except Exception as e:
            print(f"Failed to create output directory: {str(e)}")
    
    # Array to store results
    results = []
    
    # Current session count
    session_count = 0
    
    # Create a new chat window to start with
    print("\n[INFO] Creating new chat to start batch processing...")
    success = create_new_chat()
    if not success:
        print("[WARNING] Failed to create new chat, will try to use current chat")
    
    # Wait for new chat window to load
    time.sleep(2)
    
    # Process each prompt
    for i, prompt in enumerate(prompts):
        print(f"\n[{i + 1}/{len(prompts)}] Sending prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
        
        # Check if we need to create a new chat
        if config["new_chat_after_prompts"] > 0 and i > 0 and i % config["new_chat_after_prompts"] == 0:
            print(f"\n[INFO] Sent {config['new_chat_after_prompts']} prompts, creating new chat...")
            success = create_new_chat()
            
            if success:
                # Increment session count
                session_count += 1
                # Wait for new chat window to load
                time.sleep(2)
            else:
                print("[WARNING] Failed to create new chat, will continue in current chat")
        
        try:
            # Send prompt and wait for response
            print("[WAIT] Waiting for ChatGPT response...")
            response = ask_chatgpt(prompt, config)
            
            # Save results
            result_data = {
                "prompt": config["prompt_prefix"] + prompt if config["add_prefix"] else prompt,
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "session": session_count
            }
            
            results.append(result_data)
            
            # Save each result
            if config["save_results"]:
                filename = f"prompt_{i+1}_session_{session_count}_{datetime.now().isoformat().replace(':', '-')}.json"
                file_path = os.path.join(config["output_dir"], filename)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                
                print(f"Result saved to: {file_path}")
            
            # If not the last prompt, wait before continuing
            if i < len(prompts) - 1:
                print(f"\n[WAIT] Waiting {config['prompt_interval']} seconds before sending next prompt...")
                time.sleep(config["prompt_interval"])
        except Exception as e:
            print(f"Error processing prompt #{i + 1}: {str(e)}")
            
            # Record error
            error_data = {
                "prompt": config["prompt_prefix"] + prompt if config["add_prefix"] else prompt,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "session": session_count
            }
            
            results.append(error_data)
            
            # Continue to next prompt
            if i < len(prompts) - 1:
                print(f"\n[WAIT] Waiting {config['prompt_interval']} seconds before attempting next prompt...")
                time.sleep(config["prompt_interval"])
    
    print("\n==== Batch processing complete ====")
    print(f"Processed {len(results)} prompts using {session_count + 1} chat sessions")
    
    # Save summary of all results
    if config["save_results"]:
        summary_path = os.path.join(config["output_dir"], f"summary_{datetime.now().isoformat().replace(':', '-')}.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Summary results saved to: {summary_path}")
    
    return results


def load_prompts_from_file(file_path, config):
    """Load prompts list from file, create sample file if it doesn't exist"""
    if not os.path.exists(file_path):
        print(f"Prompts file '{file_path}' doesn't exist")
        create_option = input("Create sample prompts file? (y/n): ")
        if create_option.lower() == 'y':
            if create_sample_prompts_file(file_path):
                print(f"Sample prompts file created: {file_path}")
            else:
                return []
        else:
            print("No prompts file created, exiting batch processing")
            return []
    
    try:
        print(f"[LOAD] Loading prompts from \"{file_path}\"...")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse as JSON
        try:
            json_data = json.loads(content)
            if isinstance(json_data, list):
                return json_data
            elif isinstance(json_data, dict) and "prompts" in json_data and isinstance(json_data["prompts"], list):
                return json_data["prompts"]
        except json.JSONDecodeError:
            # If not JSON, split by lines
            return [line.strip() for line in content.split('\n') 
                   if line.strip() and not line.strip().startswith('#')]
        
        # If unable to parse, return empty array
        return []
    except Exception as e:
        print(f"Error loading prompts from file: {str(e)}")
        return []


def ask_single_question(config):
    """Ask a single question"""
    prompt = input("\nEnter your question: ")
    if not prompt.strip():
        print("Question cannot be empty")
        return
        
    print("\nWaiting for ChatGPT response...")
    try:
        # Create new chat
        create_new_chat()
        time.sleep(1)
        
        # Send question
        response = ask_chatgpt(prompt, config)
        
        # Save results
        if config["save_results"]:
            result_data = {
                "prompt": config["prompt_prefix"] + prompt if config["add_prefix"] else prompt,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
            os.makedirs(config["output_dir"], exist_ok=True)
            file_path = os.path.join(config["output_dir"], f"single_question_{datetime.now().isoformat().replace(':', '-')}.json")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            print(f"Result saved to: {file_path}")
    except Exception as e:
        print(f"Error getting response: {str(e)}")


def batch_question_from_file(config):
    """Batch process questions from file"""
    file_path = input(f"\nEnter the file path containing prompt list (press Enter to use default path \"{config['default_prompts_file']}\"): ")
    
    # If no path entered, use default path
    actual_file_path = file_path.strip() or config["default_prompts_file"]
    
    # Load prompts
    prompts = load_prompts_from_file(actual_file_path, config)
    
    if len(prompts) == 0:
        print("No valid prompts found in file")
        return
    
    print(f"\nLoaded {len(prompts)} prompts from file:")
    for i, prompt in enumerate(prompts):
        print(f"{i + 1}. {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    
    # Confirm to begin
    input("\nPress Enter to start batch processing...")
    batch_ask_questions(prompts, config)


def show_menu():
    """Display simplified main menu"""
    config = load_config()
    
    print("\n==== ChatGPT Simplified Batch CLI ====")
    print("1. Ask Single Question")
    print("2. Batch Process (from file)")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ")
    
    if choice == "1":
        ask_single_question(config)
        return True
    elif choice == "2":
        batch_question_from_file(config)
        return True
    elif choice == "3":
        print("Thank you for using the script, goodbye!")
        return False
    else:
        print("Invalid selection, please try again")
        return True


def main():
    """Main function"""
    print('Checking if ChatGPT is running...')
    
    if check_chatgpt_running():
        running = True
        while running:
            running = show_menu()
    else:
        print('Cannot access ChatGPT application, please make sure it is installed and can be launched.')


if __name__ == "__main__":
    main()