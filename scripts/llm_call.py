#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
llm_caller.py

Demonstration of how to send text and image inputs to different LLM providers 
(e.g., OpenAI or ApiYi) with a single high-level interface.

Key points:
1) You can switch providers via the 'provider' argument ("openai" or "apiyi").
2) If you choose ApiYi, we encode the local image as base64 and include it in the message content.
3) If you choose OpenAI, you could similarly encode and pass the image, though the current 
   public OpenAI ChatCompletion API does not officially support direct image upload.
"""

import os
import json
import openai
import requests
import base64
from PIL import Image
import io

# ----------------------------------------------------------------------
# Basic utility functions
# ----------------------------------------------------------------------

def load_config(config_path="config.json") -> dict:
    """
    Load a JSON config file which may look like this:
    {
        "openai_api_key": "sk-XXXX",
        "apiyi_api_key": "YOUR-APIYI-KEY"
    }
    """
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def encode_image_to_base64(image_path: str) -> str:
    """
    Reads the image file and returns a data URI (base64-encoded) string like:
    'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgA...'
    """
    with open(image_path, "rb") as f:
        img_bytes = f.read()
    encoded = base64.b64encode(img_bytes).decode("utf-8")

    # You may customize 'image/png' if needed (jpg, etc.)
    return f"data:image/png;base64,{encoded}"


def setup_openai_api(api_key: str):
    """
    Configure OpenAI API key for global usage.
    """
    openai.api_key = api_key


# ----------------------------------------------------------------------
# Provider-specific LLM call implementations
# ----------------------------------------------------------------------

def call_openai_llm(
    prompt: str,
    image_path: str = None,
    model: str = "gpt-4-vision",
    temperature: float = 0.0
) -> dict:
    """
    Example for calling OpenAI's model with optional image.
    (Note: As of now, public OpenAI GPT-4 APIs do not support direct image upload.
     This is a hypothetical function for demonstration only.)
    
    :param prompt: Text prompt to send to the model.
    :param image_path: Local path to an image file (optional).
    :param model: Model name, e.g., "gpt-4-vision" (hypothetical).
    :param temperature: Temperature for text generation.
    :return: A dict with keys {"text", "image"}.
    """
    image_bytes = None
    if image_path:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant specialized in image-based tasks."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            # Hypothetical argument to pass images. Adjust if your actual endpoint differs.
            images=[image_bytes] if image_bytes else None
        )
        message = response["choices"][0]["message"]
        text_output = message.get("content", "")
        image_output = message.get("image", None)  # hypothetical field
        return {"text": text_output, "image": image_output}

    except Exception as exc:
        print("Error calling OpenAI LLM:", exc)
        return {"text": "", "image": None}


def call_apiyi_llm(
    prompt: str,
    image_path: str = None,
    model: str = "gpt-4o-all",
    temperature: float = 0.0,
    api_key: str = None
) -> dict:
    """
    Call ApiYi's GPT-4o-all model with both text and optional image input.

    :param prompt: The text prompt for the model.
    :param image_path: Local path to an image file (optional).
    :param model: The ApiYi model name, e.g., "gpt-4o-all".
    :param temperature: Temperature for text generation (if supported).
    :param api_key: ApiYi API key.
    :return: A dict {"text": str, "image": bytes or None}.
    """
    if not api_key:
        raise ValueError("Missing ApiYi API key. Please provide it in config.json.")

    api_url = "https://vip.apiyi.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    # Build the message content. ApiYi expects a list of dicts, each containing "type" 
    # and either "text" or "image_url".
    content = [{"type": "text", "text": prompt}]

    if image_path:
        # Encode the local image file and embed as base64 data URI.
        base64_image = encode_image_to_base64(image_path)
        content.append({
            "type": "image",
            "image_url": {
                "url": base64_image
            }
        })

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ]
        # If ApiYi supports temperature, add it here:
        # "temperature": temperature
    }

    try:
        resp = requests.post(api_url, headers=headers, data=json.dumps(payload), timeout=6000)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        print("Error calling ApiYi LLM:", exc)
        return {"text": "", "image": None}

    # Parse ApiYi response
    if "choices" not in data or not data["choices"]:
        return {"text": "", "image": None}

    content_list = data["choices"][0]["message"]["content"]
    text_output = []
    image_output = None

    if isinstance(content_list,str):
        return {"text": content_list, "image": None}
    else:
        for item in content_list:
            ctype = item.get("type", "")
            if ctype == "text":
                text_output.append(item.get("text", ""))
            elif ctype == "image_url":
                # Usually a base64 data URI is returned here.
                image_url = item["image_url"]["url"]
                if image_url.startswith("data:image"):
                    base64_part = image_url.split(",", 1)[1]
                    image_output = base64.b64decode(base64_part)

    joined_text = "\n".join(text_output)
    return {"text": joined_text, "image": image_output}


# ----------------------------------------------------------------------
# Unified call function
# ----------------------------------------------------------------------

def call_llm(
    prompt: str,
    image_path: str = None,
    provider: str = "openai",
    config: dict = None,
    **kwargs
) -> dict:
    """
    A unified interface for calling different LLM providers.

    :param prompt: The text prompt.
    :param image_path: If needed, local image file path.
    :param provider: Which LLM provider ("openai" or "apiyi").
    :param config: Configuration dict from load_config(). Must contain relevant API keys.
    :param kwargs: Additional arguments passed to the specific call function 
                   (e.g., model, temperature).
    :return: dict, e.g. {"text": ..., "image": ...}.
    """
    if provider == "openai":
        # Make sure openai.api_key is set externally via setup_openai_api().
        return call_openai_llm(prompt,
                               image_path=image_path,
                               model=kwargs.get("model", "gpt-4-vision"),
                               temperature=kwargs.get("temperature", 0.0))

    if provider == "apiyi":
        if not config:
            raise ValueError("No config provided. ApiYi requires an API key.")
        return call_apiyi_llm(prompt,
                              image_path=image_path,
                              model=kwargs.get("model", "gpt-4o-all"),
                              temperature=kwargs.get("temperature", 0.0),
                              api_key=config.get("apiyi_api_key"))

    raise ValueError(f"Unsupported provider: {provider}")


# ----------------------------------------------------------------------
# Specific high-level function for depth estimation
# ----------------------------------------------------------------------

def llm_depth_estimation(
    image_path: str,
    prompt_file: str = "prompts/monocular_depth_estimation.txt",
    provider: str = "openai",
    model: str = None,
    temperature: float = 0.0,
    config: dict = None
) -> tuple:
    """
    Example high-level API for monocular depth estimation. 
    It reads the prompt from a file, then calls the chosen LLM with text + image input.

    :param image_path: Local path to the input RGB image.
    :param prompt_file: Path to a text file with the depth-estimation prompt.
    :param provider: "openai" or "apiyi".
    :param model: Model name, e.g. "gpt-4-vision" or "gpt-4o-all".
    :param temperature: Temperature for text generation.
    :param config: A dictionary from load_config(), containing necessary API keys.
    :return: (output_text, output_image_bytes).
    """
    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_text = f.read()

    response = call_llm(prompt_text,
                        image_path=image_path,
                        provider=provider,
                        config=config,
                        model=model,
                        temperature=temperature)

    return response.get("text", ""), response.get("image", None)


# ----------------------------------------------------------------------
# Example main
# ----------------------------------------------------------------------

def main():
    """
    Demo usage: 
    1) Load config 
    2) Optionally configure OpenAI if needed 
    3) Attempt a depth estimation call 
    """
    # 1) Load the JSON config
    config = load_config("config.json")

    # 2) If you're using OpenAI, set up the API key
    if "openai_api_key" in config and config["openai_api_key"]:
        setup_openai_api(config["openai_api_key"])

    # 3) Run an example depth estimation call
    test_image_path = "data/example/rgb/1.png"

    # Switch 'provider' to "apiyi" if you prefer
    # output = call_apiyi_llm(
    #     prompt="what foundation model are you",
    #     model="gpt-4o-mini",
    #     api_key=config["apiyi_api_key"]
    # )
    # print(output)
    text_output, depth_map_output = llm_depth_estimation(
        image_path=test_image_path,
        prompt_file="prompts/monocular_depth_estimation.txt",
        provider="apiyi",       # or "apiyi"
        model="gpt-4o-all",    # or "gpt-4o-all"
        temperature=0.0,
        config=config
    )

    print("LLM Output Text:\n", text_output)

    if depth_map_output:
        os.makedirs("outputs/images", exist_ok=True)
        output_path = "outputs/images/generated_depth_map.png"
        with open(output_path, "wb") as f:
            f.write(depth_map_output)
        print(f"Depth map image saved to: {output_path}")


if __name__ == "__main__":
    main()