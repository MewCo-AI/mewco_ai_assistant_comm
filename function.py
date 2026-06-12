import re
import sys
import keyboard as kb
import pygame as pg
from datetime import datetime
from openai import OpenAI
from pycaw.pycaw import AudioUtilities
from PySide6.QtWidgets import QApplication
from qrcode.main import QRCode
from zai import ZhipuAiClient
from gui_set import *

audio_device = AudioUtilities.GetSpeakers()
volume = audio_device.EndpointVolume
text_to_sd_prompt = "你是一个专业且高水平的Stable Diffusion AI绘画提示词生成器，擅长把我的自然语言转换成Stable Diffusion AI绘画英文提示词。回答只需输出AI绘画英文提示词，提示词由英文单词组成，用英文逗号隔开，不要输出其他内容。"


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def on_closing():
    if messagebox.askokcancel("确认退出", "您确定要退出枫云AI助手吗？"):
        root.destroy()


def open_pet():
    def open_pet_th():
        try:
            app = QApplication(sys.argv)
            pet_window = Live2dPet()
            pet_window.show()
            sys.exit(app.exec())
        except Exception:
            messagebox.showinfo("提示", "由于桌宠模块自身原因\n请重启软件再打开桌宠")

    Thread(target=open_pet_th).start()


def stream_insert(text):
    def show_in_pet():
        for window in QApplication.topLevelWidgets():
            if isinstance(window, Live2dPet):
                text2 = text.replace("\n", "").replace(f"{asst_name}:", "").strip()
                window.show_chat_response(text2)
                wait_time = len(text2) / 4
                if wait_time > 30:
                    wait_time = 30
                time.sleep(wait_time)
                break

    def insert_char(char):
        output_box.insert("end", char)
        output_box.see("end")

    def threaded_insert():
        if pet_subtitle_switch == "开启":
            Thread(target=show_in_pet).start()
        for char in text:
            insert_char(char)
            time.sleep(0.01)

    Thread(target=threaded_insert).start()


def export_chat():
    chat_records = output_box.get("1.0", "end")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = fd.asksaveasfilename(defaultextension='.txt', filetypes=[('Text Files', '*.txt')],
                                     initialfile=f'枫云AI助手{asst_name}对话记录{timestamp}')
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as chat_file:
            chat_file.write(chat_records)
            notice(f"{asst_name}对话记录导出成功")


def up_photo():
    file_path = fd.askopenfilename(title="选择一张PNG图片提问AI", filetypes=[("PNG文件", "*.png")])
    if file_path:
        target_path = "data/cache/cache.png"
        shutil.copy(file_path, target_path)
        notice(f"图片上传成功，请发送包含“图片”二字的消息提问AI")
        messagebox.showinfo("提示", "图片上传成功\n请发送包含“图片”二字的消息提问AI")


def open_chatweb():
    wb.open(f"http://127.0.0.1:{chatweb_port}")


def cloud_function_llm(function_prompt, msg):
    client = ZhipuAiClient(api_key=glm_key)
    messages = [{"role": "user", "content": msg}, {"role": "system", "content": function_prompt}]
    completion = client.chat.completions.create(model=glm_llm_model, messages=messages, thinking={"type": "disabled"})
    return completion.choices[0].message.content.replace("#", "").replace("*", "").strip()


def function_llm(function_prompt, msg):
    function_prompt = function_prompt + "/no_think"
    messages = [{"role": "system", "content": function_prompt}, {"role": "user", "content": msg}]
    try:
        if llm_menu.get() == "GLM-4.7-Flash":
            client = ZhipuAiClient(api_key=glm_key)
            completion = client.chat.completions.create(model=glm_llm_model, messages=messages, thinking={"type": "disabled"})
        elif llm_menu.get() == "千问Qwen3-8B":
            client = OpenAI(base_url=sf_url, api_key=sf_key)
            completion = client.chat.completions.create(model="Qwen/Qwen3-8B", messages=messages)
        elif llm_menu.get() == "千问Qwen3.5-4B":
            client = OpenAI(base_url=sf_url, api_key=sf_key)
            completion = client.chat.completions.create(model="Qwen/Qwen3.5-4B", messages=messages,
                                                        extra_body={"enable_thinking": False})
        elif llm_menu.get() == "星火Lite":
            client = OpenAI(base_url=xf_url, api_key=xf_key)
            completion = client.chat.completions.create(model=xf_model, messages=messages)
        elif llm_menu.get() == "本地LM Studio":
            client = OpenAI(base_url=f"http://{local_llm_ip}:{lmstudio_port}/v1", api_key="lm-studio")
            completion = client.chat.completions.create(model="", messages=messages)
        elif llm_menu.get() == "本地KoboldCpp":
            client = OpenAI(base_url=f"http://{local_llm_ip}:{kobold_port}/v1", api_key="koboldcpp")
            completion = client.chat.completions.create(model="", messages=messages)
        elif llm_menu.get() == "本地llama.cpp":
            client = OpenAI(base_url=f"http://{local_llm_ip}:{llamacpp_port}/v1", api_key="llamacpp")
            completion = client.chat.completions.create(model="", messages=messages)
        elif llm_menu.get() == "本地Transformers":
            client = OpenAI(base_url=f"http://{local_llm_ip}:{tf_port}/v1", api_key="transformers")
            completion = client.chat.completions.create(model=tf_model, messages=messages)
            chunks = re.findall(r'^data:\s*(.+)$', completion, flags=re.MULTILINE)
            result_content = []
            for chunk in chunks:
                try:
                    data = json.loads(chunk)
                    content = data.get("choices", [{}])[0].get("delta", {}).get("content")
                    if content is not None:
                        result_content.append(content)
                except json.JSONDecodeError:
                    continue
            res = "".join(result_content).replace("\n", "")
            if think_filter_switch == "开启":
                res = res.split("</think>")[-1].strip()
            return res.replace("#", "").replace("*", "")
        elif llm_menu.get() == "本地Ollama LLM":
            client = OpenAI(base_url=f'http://{local_llm_ip}:{ollama_port}/v1', api_key="ollama")
            completion = client.chat.completions.create(model=ollama_model_name, messages=messages)
        elif llm_menu.get() == "自定义API-LLM":
            client = OpenAI(base_url=custom_llm_url, api_key=custom_llm_key)
            completion = client.chat.completions.create(model=custom_llm_model, messages=messages,
                                                        extra_body={"thinking": {"type": "disabled"},
                                                                    "enable_thinking": False})
        else:
            return f"[{llm_menu.get()}未适配{mode_menu.get()}，可选择其他对话模型]"
        res = completion.choices[0].message.content
        if think_filter_switch == "开启":
            res = res.split("</think>")[-1].strip()
        return res.replace("#", "").replace("*", "").strip()
    except Exception as e:
        return f"[{llm_menu.get()}配置错误，可选择其他对话模型，错误详情：{e}]"


def voice_input(text):
    content = text.replace("语音输入", "")
    for char in content:
        kb.write(char)
        time.sleep(0.01)


def vol_up():
    try:
        current_volume = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(current_volume + 0.15, None)
        current_volume += 0.15
        res = f"{asst_name}已把[音量]调大至{int(current_volume * 100)}%"
        notice(res)
        return res
    except:
        res = f"{asst_name}已把[音量]调至最大"
        notice(res)
        return res


def vol_down():
    try:
        current_volume = volume.GetMasterVolumeLevelScalar()
        volume.SetMasterVolumeLevelScalar(current_volume - 0.15, None)
        current_volume -= 0.15
        res = f"{asst_name}已把[音量]调小至{int(current_volume * 100)}%"
        notice(res)
        return res
    except:
        res = f"{asst_name}已把[音量]调至最小"
        notice(res)
        return res


def open_vmd_music():  # 打开MMD 3D动作音乐
    wb.open(f"http://127.0.0.1:{mmd_port}/vmd")
    if vmd_music_switch == "开启":
        pg.mixer.init()
        try:
            vmd_music = pg.mixer.Sound(f'data/music_vmd/{vmd_music_name}')
            vmd_music.play()
        except:
            messagebox.showinfo("MMD 3D音乐名称配置错误", "请前往软件设置→更多设置正确配置MMD 3D动作音乐")


def open_web_tips():
    def create_qrcode_with_logo(url):
        qr = QRCode(version=1, error_correction=2, box_size=5, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        logo = Image.open(logo_path)
        qr_width, qr_height = img.size
        logo_size = min(qr_width, qr_height) // 5
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
        img.paste(logo, pos)
        return img

    global web_box_w
    web_box_w = tk.Toplevel(root)
    web_box_w.geometry("660x660")
    web_box_w.attributes("-topmost", 1)
    web_box_w.title("手机网页访问 - 枫云AI助手社区版")
    msg_text = ScrolledText(web_box_w, wrap=tk.WORD)
    msg_text.pack(fill='both', expand=True)
    text1 = "使用手机访问枫云AI助手，无需下载APP\n\n保持手机和本电脑处于同一WiFi/局域网\n\n根据需求，在手机浏览器输入下面网址即可便捷访问："
    text2 = f"http://{server_ip}:{chatweb_port}"
    text3 = "不仅手机能访问，\n同一WiFi或局域网下的电脑/平板/电视/手表/车机如果内置浏览器，\n也可通过输入上述网址访问枫云AI助手\n\n网页端在非本电脑的其他设备上默认情况下仅支持打字聊天和显示角色，不支持语音识别和摄像头识别。如需串流其他设备，推荐使用AudioRelay和iVCam软件\n\n也可手机扫描下面二维码便捷访问：\n"
    text = text1 + "\n\n" + text2 + "\n\n" + text3
    logo_path = "data/image/logo.png"
    qr_img = create_qrcode_with_logo(text2)
    qr_photo = ImageTk.PhotoImage(qr_img)
    msg_text.insert("end", text)
    msg_text.image_create("end", image=qr_photo)
    msg_text.image = qr_photo
    msg_text.configure(state="disabled")
    web_box_w.iconbitmap("data/image/logo.ico")
    web_box_w.bind("<Button-3>", show_menu_web_box)


def show_menu_web_box(event):
    menu = Menu(web_box_w, tearoff=0)
    menu.add_command(label="📄复制 Ctrl+C", command=lambda: web_box_w.focus_get().event_generate('<<Copy>>'))
    menu.post(event.x_root, event.y_root)
