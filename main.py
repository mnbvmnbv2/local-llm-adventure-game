from datetime import datetime
import requests
import urllib.request
import base64
import json
import time
import os


webui_server_url = "http://127.0.0.1:7860"

out_dir = "pics"


def timestamp():
    return datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S")


def decode_and_save_base64(base64_str: str, save_path):
    with open(save_path, "wb") as file:
        file.write(base64.b64decode(base64_str))


def call_api(api_endpoint, **payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{webui_server_url}/{api_endpoint}",
        headers={"Content-Type": "application/json"},
        data=data,
    )
    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode("utf-8"))


def call_txt2img_api(**payload):
    response = call_api("sdapi/v1/txt2img", **payload)
    for index, image in enumerate(response.get("images")):
        save_path = os.path.join(out_dir, f"txt2img-{timestamp()}-{index}.png")
        decode_and_save_base64(image, save_path)


def create_image_from_prompt(prompt: str):
    payload = {
        "prompt": prompt,
        "negative_prompt": "",
        "seed": 1,
        "steps": 20,
        "width": 768,
        "height": 768,
        "cfg_scale": 7,
        "sampler_name": "Euler a",
        "n_iter": 1,
        "batch_size": 1,
    }
    call_txt2img_api(**payload)


def prompt_llm(prompt: str, llm_model: str = "llama3"):
    url = "http://localhost:11434/api/chat"
    data = {"model": llm_model, "messages": [{"role": "user", "content": prompt}]}

    response = requests.post(url, json=data)

    response_text = response.text
    # Split the response into individual JSON objects
    json_objects = response_text.strip().split("\n")

    # Extract and combine the message contents
    messages = []
    for obj in json_objects:
        json_obj = json.loads(obj)
        if "message" in json_obj and "content" in json_obj["message"]:
            messages.append(json_obj["message"]["content"])

    # Combine the messages into a single string
    combined_message = "".join(messages)

    print(combined_message)

    create_image_from_prompt(combined_message)


if __name__ == "__main__":
    prompt = input("Enter a prompt: ")
    prompt_llm(prompt)
