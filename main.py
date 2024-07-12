from datetime import datetime
import requests
import urllib.request
import base64
import json
import time
import os

import sys

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QApplication,
)
from PyQt5.QtGui import QPixmap


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # Main
        main_layout = QVBoxLayout()
        self.text_label = QLabel("Here comes the LLM text")
        main_layout.addWidget(self.text_label)

        # Image display
        self.image_label = QLabel("Image will be displayed here")
        self.image_label.setPixmap(QPixmap())  # Placeholder for an image
        main_layout.addWidget(self.image_label)

        # Text field
        self.text_input = QLineEdit("Enter your prompt here")
        main_layout.addWidget(self.text_input)

        # Prompt button
        self.prompt_button = QPushButton("Prompt")
        main_layout.addWidget(self.prompt_button)

        self.setLayout(main_layout)

        # Logic
        self.prompt_button.clicked.connect(self.prompt)

    def update_text(self, text: str):
        self.text_label.setText(text)

    def prompt(self):
        user_input = self.text_input.text()
        self.llm_prompt(user_input)

    def llm_prompt(self, prompt: str):
        response, img_path = prompt_llm(prompt)
        self.update_text(response)
        self.update_image(img_path)

    def update_image(self, image_path: str):
        pixmap = QPixmap(image_path)
        self.image_label.setPixmap(pixmap)


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
    return save_path


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
    return call_txt2img_api(**payload)


def prompt_llm(prompt: str, llm_model: str = "adv"):
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

    # split message on * to get feedback to player and image description
    response_text = combined_message.split("*")[0]
    image_description = combined_message.split("*")[1]

    save_path = create_image_from_prompt(image_description)

    return response_text, save_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    m = MainWidget()
    m.show()
    m.llm_prompt("Start the game in a random location and a random item.")
    sys.exit(app.exec_())
