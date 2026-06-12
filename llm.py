import random
from base64 import b64decode
from vlm import *

with open('data/db/memory.db', 'r', encoding='utf-8') as memory_file:
    try:
        openai_history = json.load(memory_file)
    except:
        openai_history = []


def chat_preprocess(msg):
    try:
        content = "图像识别已关闭"
        if ("屏幕" in msg or "画面" in msg or "图像" in msg or "看到" in msg or "看看" in msg or "看见" in msg
            or "照片" in msg or "摄像头" in msg or "图片" in msg) and img_menu.get() != "关闭图像识别":
            if mode_menu.get() == "提示词对话":
                msg = f"{prompt}。你需要根据其中内容和我聊天。我的问题是：{msg}"
            vlm_mapping = {
                "photo": {"GLM-4.6V-Flash": glm_4v_photo, "千问Qwen3.5-4B": qwen_vlm_photo,
                          "本地Ollama VLM": ollama_vlm_photo, "本地LM Studio": lmstudio_vlm_photo,
                          "本地KoboldCpp": kobold_vlm_photo, "本地llama.cpp": llamacpp_vlm_photo,
                          "自定义API-VLM": custom_vlm_photo},
                "screen": {"GLM-4.6V-Flash": glm_4v_screen, "千问Qwen3.5-4B": qwen_vlm_screen,
                           "本地Ollama VLM": ollama_vlm_screen, "本地LM Studio": lmstudio_vlm_screen,
                           "本地KoboldCpp": kobold_vlm_screen, "本地llama.cpp": llamacpp_vlm_screen,
                           "自定义API-VLM": custom_vlm_screen},
                "cam": {"GLM-4.6V-Flash": glm_4v_cam, "千问Qwen3.5-4B": qwen_vlm_cam, "本地Ollama VLM": ollama_vlm_cam,
                        "本地LM Studio": lmstudio_vlm_cam, "本地KoboldCpp": kobold_vlm_cam,
                        "本地llama.cpp": llamacpp_vlm_cam, "自定义API-VLM": custom_vlm_cam}}
            if any(keyword in msg for keyword in ["屏幕", "画面", "图像"]):
                selected_model = img_menu.get()
                content = vlm_mapping["screen"][selected_model](msg)
                notice(f"{asst_name}捕获了屏幕，调用[电脑屏幕识别]")
            elif "图片" in msg:
                if os.path.exists("data/cache/cache.png"):
                    selected_model = img_menu.get()
                    content = vlm_mapping["photo"][selected_model](msg)
                    notice(f"{asst_name}识别了上传的图片")
                    os.remove("data/cache/cache.png")
                else:
                    content = "请先点击右下方按钮上传图片"
                    notice("请先点击右下方按钮上传图片")
            elif any(keyword in msg for keyword in
                     ["看到", "看见", "看看", "照片", "摄像头"]) and cam_permission == "开启":
                selected_model = img_menu.get()
                content = vlm_mapping["cam"][selected_model](msg)
                notice(f"{asst_name}拍了照片，调用[摄像头识别]")
        elif "画" in msg and prefer_draw != "关闭AI绘画":
            msg = re.sub(r"画|绘画", "", msg)
            content = "正在进行AI绘画"
            notice(f"{asst_name}正在进行AI绘画，请稍等...")
            if prefer_draw == "本地SD API":
                local_sd(msg)
            elif prefer_draw == "云端CogView-3-Flash":
                cloud_cogview(msg)
            elif prefer_draw == "云端Kolors":
                cloud_kolors(msg)
            elif prefer_draw == "云端文心Web":
                content = "绘画完成"
                msg = re.sub(r"画|绘画", "", msg)
                wb.open(f'https://image.baidu.com/front/aigc?tn=aigc&word={msg}')
                notice(f"{asst_name}打开了浏览器，调用[云AI绘画]")
        else:
            if mode_menu.get() == "多智能体助手":
                content = function_llm(
                    f"{prompt}。你是{asst_name}，是专属于我({username})的多智能体助手，支持调用多种智能体，拥有以下功能：{all_task}。",
                    msg)
            elif mode_menu.get() == "自主操控Lite" or mode_menu.get() == "自主操控Pro" or mode_menu.get() == "OpenClaw龙虾" or mode_menu.get() == "MQTT/QwenPaw":
                content = "当前运行模式处于通用自主操控或龙虾模式，请使用主界面输入指令来自动化操控电脑"
            else:
                content = chat_llm(msg)
            notice(f"收到{asst_name}回复")
        MEMORY_ROUNDS_MAP = {"超长记忆": 200, "长期记忆": 100, "中期记忆": 50, "短期记忆": 25}
        limit_rounds = MEMORY_ROUNDS_MAP.get(memory_mode, 10)
        current_rounds = len(openai_history) // 2
        while current_rounds > limit_rounds:
            round_to_remove = random.randint(0, current_rounds - 1) * 2
            del openai_history[round_to_remove:round_to_remove + 2]
            current_rounds = len(openai_history) // 2  # 更新当前轮数
        with open('data/db/memory.db', 'w', encoding='utf-8') as f:
            json.dump(openai_history, f, ensure_ascii=False, indent=4)
        return content
    except Exception as e:
        notice(f"图像识别引擎配置错误，错误详情：{e}")
        return "图像识别引擎配置错误"


def chat_llm(msg):
    prompt1 = prompt + "/no_think"
    if "几点" in msg or "多少点" in msg or "时间" in msg or "时候" in msg or "日期" in msg or "多少号" in msg or "几号" in msg:
        msg = f"[当前时间:{current_time()}]{msg}"
    try:
        if llm_menu.get() == "GLM-4.7-Flash":
            client = ZhipuAiClient(api_key=glm_key)
            openai_history.append({"role": "user", "content": msg})
            messages = [{"role": "system", "content": prompt1}]
            messages.extend(openai_history)
            completion = client.chat.completions.create(model=glm_llm_model, messages=messages,
                                                        thinking={"type": "disabled"})
            openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
            return completion.choices[0].message.content.strip()
        elif llm_menu.get() == "DeepSeek-R1-8B":
            client = OpenAI(base_url=sf_url, api_key=sf_key)
            openai_history.append({"role": "user", "content": msg})
            messages = [{"role": "system", "content": prompt1}]
            messages.extend(openai_history)
            completion = client.chat.completions.create(model="deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
                                                        messages=messages)
            openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
            res = completion.choices[0].message.content
            if think_filter_switch == "开启":
                res = res.split("</think>")[-1].strip()
            return res
        elif llm_menu.get() == "千问Qwen3-8B":
            client = OpenAI(base_url=sf_url, api_key=sf_key)
            openai_history.append({"role": "user", "content": msg})
            messages = [{"role": "system", "content": prompt1}]
            messages.extend(openai_history)
            completion = client.chat.completions.create(model="Qwen/Qwen3-8B", messages=messages)
            openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
            return completion.choices[0].message.content.strip()
        elif llm_menu.get() == "千问Qwen3.5-4B":
            client = OpenAI(base_url=sf_url, api_key=sf_key)
            openai_history.append({"role": "user", "content": msg})
            messages = [{"role": "system", "content": prompt1}]
            messages.extend(openai_history)
            completion = client.chat.completions.create(model="Qwen/Qwen3.5-4B", messages=messages,
                                                        extra_body={"enable_thinking": False})
            openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
            return completion.choices[0].message.content.strip()
        elif llm_menu.get() == "星火Lite":
            client = OpenAI(base_url=xf_url, api_key=xf_key)
            openai_history.append({"role": "user", "content": msg})
            messages = [{"role": "system", "content": prompt1}]
            messages.extend(openai_history)
            completion = client.chat.completions.create(model=xf_model, messages=messages)
            openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
            return completion.choices[0].message.content
        elif llm_menu.get() == "本地Transformers":
            try:
                client = OpenAI(base_url=f"http://{local_llm_ip}:{tf_port}/v1", api_key="transformers")
                openai_history.append({"role": "user", "content": msg})
                messages = [{"role": "system", "content": prompt1}]
                messages.extend(openai_history)
                completion = client.chat.completions.create(model=tf_model, messages=messages, stream=False)
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
                result_content = "".join(result_content).replace("\n", "")
                openai_history.append({"role": "assistant", "content": result_content})
                res = result_content
                if think_filter_switch == "开启":
                    res = res.split("</think>")[-1].strip()
                return res
            except Exception as e:
                return f"本地Transformers服务未开启，错误详情：{e}"
        elif llm_menu.get() == "本地LM Studio":
            try:
                client = OpenAI(base_url=f"http://{local_llm_ip}:{lmstudio_port}/v1", api_key="lm-studio")
                openai_history.append({"role": "user", "content": msg})
                messages = [{"role": "system", "content": prompt1}]
                messages.extend(openai_history)
                completion = client.chat.completions.create(model="", messages=messages)
                openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
                res = completion.choices[0].message.content
                if think_filter_switch == "开启":
                    res = res.split("</think>")[-1].strip()
                return res
            except Exception as e:
                return f"本地LM Studio软件API服务未开启，错误详情：{e}"
        elif llm_menu.get() == "本地KoboldCpp":
            try:
                client = OpenAI(base_url=f"http://{local_llm_ip}:{kobold_port}/v1", api_key="koboldcpp")
                openai_history.append({"role": "user", "content": msg})
                messages = [{"role": "system", "content": prompt1}]
                messages.extend(openai_history)
                completion = client.chat.completions.create(model="", messages=messages)
                openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
                res = completion.choices[0].message.content
                if think_filter_switch == "开启":
                    res = res.split("</think>")[-1].strip()
                return res
            except Exception as e:
                return f"本地KoboldCpp API服务未开启，错误详情：{e}"
        elif llm_menu.get() == "本地llama.cpp":
            try:
                client = OpenAI(base_url=f"http://{local_llm_ip}:{llamacpp_port}/v1", api_key="llamacpp")
                openai_history.append({"role": "user", "content": msg})
                messages = [{"role": "system", "content": prompt1}]
                messages.extend(openai_history)
                completion = client.chat.completions.create(model="", messages=messages)
                openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
                res = completion.choices[0].message.content
                if think_filter_switch == "开启":
                    res = res.split("</think>")[-1].strip()
                return res
            except Exception as e:
                return f"本地llama.cpp API服务未开启，错误详情：{e}"
        elif llm_menu.get() == "本地Ollama LLM":
            try:
                try:
                    rq.get(f'http://{local_llm_ip}:{ollama_port}')
                except:
                    Popen(f"ollama pull {ollama_model_name}", shell=False)
                client = OpenAI(base_url=f'http://{local_llm_ip}:{ollama_port}/v1', api_key="ollama")
                openai_history.append({"role": "user", "content": msg})
                messages = [{"role": "system", "content": prompt1}]
                messages.extend(openai_history)
                completion = client.chat.completions.create(model=ollama_model_name, messages=messages)
                openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
                res = completion.choices[0].message.content
                if think_filter_switch == "开启":
                    res = res.split("</think>")[-1].strip()
                return res
            except Exception as e:
                return f"本地Ollama LLM配置错误，错误详情：{e}"
        elif llm_menu.get() == "Dify聊天助手":
            try:
                res = chat_dify(msg)
                return res
            except Exception as e:
                return f"本地Dify聊天助手配置错误，错误详情：{e}"
        elif llm_menu.get() == "AnythingLLM":
            try:
                res = chat_anything_llm(msg)
                return res
            except Exception as e:
                return f"本地AnythingLLM知识库配置错误，错误详情：{e}"
        else:
            try:
                client = OpenAI(base_url=custom_llm_url, api_key=custom_llm_key)
                openai_history.append({"role": "user", "content": msg})
                messages = [{"role": "system", "content": prompt1}]
                messages.extend(openai_history)
                completion = client.chat.completions.create(
                    model=custom_llm_model, messages=messages,
                    extra_body={"thinking": {"type": "disabled"}, "enable_thinking": False})
                openai_history.append({"role": "assistant", "content": completion.choices[0].message.content})
                res = completion.choices[0].message.content
                if think_filter_switch == "开启":
                    res = res.split("</think>")[-1].strip()
                return res.strip()
            except Exception as e:
                return f"自定义API配置错误，错误详情：{e}"
    except Exception as e:
        return f"{llm_menu.get()}未正确配置，请前往软件设置网页→Free云端AI Key正确配置，错误详情：{e}"


def chat_dify(msg):
    headers = {"Authorization": f"Bearer {dify_key}", "Content-Type": "application/json"}
    data = {"query": msg, "inputs": {}, "response_mode": "blocking", "user": username, "conversation_id": None}
    res = rq.post(f"http://{dify_ip}/v1/chat-messages", headers=headers, data=json.dumps(data))
    res = res.json()['answer'].strip()
    if think_filter_switch == "开启":
        res = res.split("</think>")[-1].strip()
    return res


def chat_anything_llm(msg):
    url = f"http://{local_llm_ip}:3001/api/v1/workspace/{anything_llm_ws}/chat"
    headers = {"Authorization": f"Bearer {anything_llm_key}", "Content-Type": "application/json"}
    data = {"message": msg, "mode": "chat"}
    res = rq.post(url, json=data, headers=headers)
    res = res.json().get("textResponse")
    if think_filter_switch == "开启":
        res = res.split("</think>")[-1].strip()
    return res


def clear_chat():
    global openai_history
    if messagebox.askokcancel(f"清除{asst_name}的聊天记录",
                              f"您确定要清除{asst_name}的聊天记录吗？\n如有需要可先点击🔼导出记录再开启新对话\n(该操作不影响助手记忆，\n如果想删除记忆可右键聊天框)"):
        output_box.delete("1.0", "end")
        notice("聊天记录已清空")


def local_sd(msg):
    def local_sd_th():
        try:
            sd_prompt = function_llm(text_to_sd_prompt,
                                     f"请你根据我的下述需求生成AI绘画提示词，提示词由英文单词组成，用英文逗号隔开，不要输出其他内容：{msg}")
            payload = {"prompt": sd_prompt, "steps": 20}
            res = rq.post(f"http://{local_draw_ip}:{sd_port}/sdapi/v1/txt2img", json=payload)
            data = res.json()
            sd_draw_path = "data/cache/draw/sd_aigc.png"
            with open(sd_draw_path, 'wb') as f:
                f.write(b64decode(data['images'][0]))
            notice("绘画完成")
            draw_box("Stable Diffusion", "sd_aigc")
        except Exception as e:
            notice(f"本地SD AI绘画出错，错误详情：{e}")

    Thread(target=local_sd_th).start()


def cloud_cogview(msg):
    def cloud_cogview_th():
        try:
            client = ZhipuAiClient(api_key=glm_key)
            res = client.images.generations(model="cogview-3-flash", prompt=msg)
            image_response = rq.get(res.data[0].url)
            cogview_draw_path = "data/cache/draw/cogview_aigc.png"
            with open(cogview_draw_path, "wb") as f:
                f.write(image_response.content)
            notice("绘画完成")
            draw_box("CogView", "cogview_aigc")
        except:
            notice("云端Cogview绘画服务拥挤，可选择其他图像生成引擎")

    Thread(target=cloud_cogview_th).start()


def cloud_kolors(msg):
    def cloud_kolors_th():
        try:
            url = f"{sf_url}/images/generations"
            payload = {"model": "Kwai-Kolors/Kolors", "prompt": msg}
            headers = {"Authorization": f"Bearer {sf_key}", "Content-Type": "application/json"}
            res = rq.request("POST", url, json=payload, headers=headers)
            image_response = rq.get(res.json()["images"][0]["url"])
            kolors_draw_path = "data/cache/draw/kolors_aigc.png"
            with open(kolors_draw_path, "wb") as f:
                f.write(image_response.content)
            notice("绘画完成")
            draw_box("Kolors", "kolors_aigc")
        except:
            notice("云端Kolors绘画服务拥挤，可选择其他图像生成引擎")

    Thread(target=cloud_kolors_th).start()
