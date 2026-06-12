import cv2
import numpy as np
from base64 import b64encode
from subprocess import Popen
from typing import Callable, Dict
from function import *

PHOTO_PATH = "data/cache/cache.png"
IMAGE_FORMAT_CAM = "jpg"
IMAGE_FORMAT_SCREEN = "jpg"
IMAGE_FORMAT_PHOTO = "png"


def encode_image(image, image_format: str = "jpg") -> str:
    _, buffer = cv2.imencode(f'.{image_format}', image)
    return b64encode(buffer).decode('utf-8')


def encode_image_from_file(file_path: str) -> str:
    with open(file_path, "rb") as image_file:
        return b64encode(image_file.read()).decode('utf-8')


def get_camera_frame() -> np.ndarray | None:
    cap = cv2.VideoCapture(cam_num)
    if not cap.isOpened():
        cap.release()
        return None
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None


def get_screenshot_bgr() -> np.ndarray:
    screenshot = pag.screenshot()
    screenshot_np = np.array(screenshot)
    return cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)


def build_vlm_messages(question: str, base64_img: str, img_format: str) -> list:
    return [{"role": "user", "content": [{"type": "text", "text": question}, {"type": "image_url", "image_url": {
        "url": f"data:image/{img_format};base64,{base64_img}"}}]}]


def glm_4v_handler(question: str, base64_img: str, img_format: str) -> str:
    messages = build_vlm_messages(question, base64_img, img_format)
    vlm_client = ZhipuAiClient(api_key=glm_key)
    completion = vlm_client.chat.completions.create(model=glm_vlm_model, messages=messages,
                                                    thinking={"type": "disabled"})
    return completion.choices[0].message.content


def ollama_vlm_handler(question: str, base64_img: str, img_format: str) -> str:
    try:
        rq.get(f'http://{local_vlm_ip}:{ollama_port}/v1')
    except:
        Popen(f"ollama pull {ollama_vlm_name}", shell=False)
    messages = build_vlm_messages(question, base64_img, img_format)
    vlm_client = OpenAI(base_url=f"http://{local_vlm_ip}:{ollama_port}/v1", api_key="ollama")
    completion = vlm_client.chat.completions.create(model=ollama_vlm_name, messages=messages)
    return completion.choices[0].message.content


def qwen_vlm_handler(question: str, base64_img: str, img_format: str) -> str:
    messages = build_vlm_messages(question, base64_img, img_format)
    vlm_client = OpenAI(base_url=sf_url, api_key=sf_key)
    completion = vlm_client.chat.completions.create(model="Qwen/Qwen3.5-4B", messages=messages,
                                                    extra_body={"enable_thinking": False})
    return completion.choices[0].message.content


def lmstudio_vlm_handler(question: str, base64_img: str, img_format: str) -> str:
    messages = build_vlm_messages(question, base64_img, img_format)
    vlm_client = OpenAI(base_url=f"http://{local_vlm_ip}:{lmstudio_port}/v1", api_key="lm-studio")
    completion = vlm_client.chat.completions.create(model="", messages=messages)
    return completion.choices[0].message.content


def kobold_vlm_handler(question: str, base64_img: str, img_format: str) -> str:
    messages = build_vlm_messages(question, base64_img, img_format)
    vlm_client = OpenAI(base_url=f"http://{local_vlm_ip}:{kobold_port}/v1", api_key="koboldcpp")
    completion = vlm_client.chat.completions.create(model="", messages=messages)
    return completion.choices[0].message.content


def llamacpp_vlm_handler(question: str, base64_img: str, img_format: str) -> str:
    messages = build_vlm_messages(question, base64_img, img_format)
    vlm_client = OpenAI(base_url=f"http://{local_vlm_ip}:{llamacpp_port}/v1", api_key="llamacpp")
    completion = vlm_client.chat.completions.create(model="", messages=messages)
    return completion.choices[0].message.content


def custom_vlm_handler(question: str, base64_img: str, img_format: str) -> str:
    messages = build_vlm_messages(question, base64_img, img_format)
    vlm_client = OpenAI(base_url=custom_vlm_url, api_key=custom_vlm_key)
    completion = vlm_client.chat.completions.create(model=custom_vlm_model, messages=messages,
                                                    extra_body={"thinking": {"type": "disabled"},
                                                                "enable_thinking": False})
    return completion.choices[0].message.content


def glm_4v_cam(question):
    frame = get_camera_frame()
    if frame is None:
        return "无法打开摄像头"
    return glm_4v_handler(question, encode_image(frame, IMAGE_FORMAT_CAM), IMAGE_FORMAT_CAM)


def glm_4v_screen(question):
    screenshot = get_screenshot_bgr()
    return glm_4v_handler(question, encode_image(screenshot, IMAGE_FORMAT_SCREEN), IMAGE_FORMAT_SCREEN)


def glm_4v_photo(question):
    return glm_4v_handler(question, encode_image_from_file(PHOTO_PATH), IMAGE_FORMAT_PHOTO)


def ollama_vlm_cam(question):
    frame = get_camera_frame()
    if frame is None:
        return "无法打开摄像头"
    return ollama_vlm_handler(question, encode_image(frame, IMAGE_FORMAT_CAM), IMAGE_FORMAT_CAM)


def ollama_vlm_screen(question):
    screenshot = get_screenshot_bgr()
    return ollama_vlm_handler(question, encode_image(screenshot, IMAGE_FORMAT_SCREEN), IMAGE_FORMAT_SCREEN)


def ollama_vlm_photo(question):
    return ollama_vlm_handler(question, encode_image_from_file(PHOTO_PATH), IMAGE_FORMAT_PHOTO)


def qwen_vlm_cam(question):
    frame = get_camera_frame()
    if frame is None:
        return "无法打开摄像头"
    return qwen_vlm_handler(question, encode_image(frame, IMAGE_FORMAT_CAM), IMAGE_FORMAT_CAM)


def qwen_vlm_screen(question):
    screenshot = get_screenshot_bgr()
    return qwen_vlm_handler(question, encode_image(screenshot, IMAGE_FORMAT_SCREEN), IMAGE_FORMAT_SCREEN)


def qwen_vlm_photo(question):
    return qwen_vlm_handler(question, encode_image_from_file(PHOTO_PATH), IMAGE_FORMAT_PHOTO)


def lmstudio_vlm_cam(question):
    frame = get_camera_frame()
    if frame is None:
        return "无法打开摄像头"
    return lmstudio_vlm_handler(question, encode_image(frame, IMAGE_FORMAT_CAM), IMAGE_FORMAT_CAM)


def lmstudio_vlm_screen(question):
    screenshot = get_screenshot_bgr()
    return lmstudio_vlm_handler(question, encode_image(screenshot, IMAGE_FORMAT_SCREEN), IMAGE_FORMAT_SCREEN)


def lmstudio_vlm_photo(question):
    return lmstudio_vlm_handler(question, encode_image_from_file(PHOTO_PATH), IMAGE_FORMAT_PHOTO)


def kobold_vlm_cam(question):
    frame = get_camera_frame()
    if frame is None:
        return "无法打开摄像头"
    return kobold_vlm_handler(question, encode_image(frame, IMAGE_FORMAT_CAM), IMAGE_FORMAT_CAM)


def kobold_vlm_screen(question):
    screenshot = get_screenshot_bgr()
    return kobold_vlm_handler(question, encode_image(screenshot, IMAGE_FORMAT_SCREEN), IMAGE_FORMAT_SCREEN)


def kobold_vlm_photo(question):
    return kobold_vlm_handler(question, encode_image_from_file(PHOTO_PATH), IMAGE_FORMAT_PHOTO)


def llamacpp_vlm_cam(question):
    frame = get_camera_frame()
    if frame is None:
        return "无法打开摄像头"
    return llamacpp_vlm_handler(question, encode_image(frame, IMAGE_FORMAT_CAM), IMAGE_FORMAT_CAM)


def llamacpp_vlm_screen(question):
    screenshot = get_screenshot_bgr()
    return llamacpp_vlm_handler(question, encode_image(screenshot, IMAGE_FORMAT_SCREEN), IMAGE_FORMAT_SCREEN)


def llamacpp_vlm_photo(question):
    return llamacpp_vlm_handler(question, encode_image_from_file(PHOTO_PATH), IMAGE_FORMAT_PHOTO)


def custom_vlm_cam(question):
    frame = get_camera_frame()
    if frame is None:
        return "无法打开摄像头"
    return custom_vlm_handler(question, encode_image(frame, IMAGE_FORMAT_CAM), IMAGE_FORMAT_CAM)


def custom_vlm_screen(question):
    screenshot = get_screenshot_bgr()
    return custom_vlm_handler(question, encode_image(screenshot, IMAGE_FORMAT_SCREEN), IMAGE_FORMAT_SCREEN)


def custom_vlm_photo(question):
    return custom_vlm_handler(question, encode_image_from_file(PHOTO_PATH), IMAGE_FORMAT_PHOTO)


def function_vlm(msg):
    vlm_handlers: Dict[str, Callable] = {
        "GLM-4.6V-Flash": glm_4v_screen, "千问Qwen3.5-4B": qwen_vlm_screen, "本地Ollama VLM": ollama_vlm_screen,
        "本地LM Studio": lmstudio_vlm_screen, "本地KoboldCpp": kobold_vlm_screen, "本地llama.cpp": llamacpp_vlm_screen}
    try:
        handler = vlm_handlers.get(img_menu.get(), custom_vlm_screen)
        return handler(msg).replace("#", "").replace("*", "")
    except Exception as e:
        return f"图像识别引擎配置错误，错误详情：{e}"
