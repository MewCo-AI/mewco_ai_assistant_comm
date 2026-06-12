import ctypes
import json
import logging
import socket
import shutil
from threading import Thread
from tkinter import filedialog as fd, messagebox
from flask import Flask, render_template_string, request, jsonify, send_from_directory

with open('data/db/init.db', 'r', encoding='utf-8') as f_init:
    lines = f_init.readlines()
init = int(lines[0].strip())
if init == 0:
    user_response = messagebox.askyesno("欢迎使用枫云AI助手社区版",
                                        "您是否阅读了软件使用文档并同意GPL-3.0开源协议？\n(首次运行加载较长,请耐心等待)\n注意事项:\n1.如果需要使用云端免费模型,首次使用请前往软件设置网页→Free云端AI Key\n2.本软件公益开源免费,严禁商用、套壳和倒卖,请遵守开源协议使用")
    if user_response:
        with open('data/db/init.db', 'w', encoding="utf-8") as f_init:
            f_init.write("1")
    else:
        exit()

app_set = Flask(__name__, static_folder='dist')
logging.getLogger('werkzeug').setLevel(logging.ERROR)
CONFIG_FILE = 'data/db/config.json'


def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载配置失败: {e}，将使用默认配置")
        return default_config


def save_config(config_data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存设置失败: {e}")
        return False


@app_set.route('/')
def index_set():
    with open("dist/web_settings.html", 'r', encoding='utf-8') as f:
        html_settings = f.read()
    return render_template_string(html_settings)


@app_set.route('/get_config')
def get_config():
    cfg = load_config()
    return jsonify(cfg)


@app_set.route('/save_config', methods=['POST'])
def save_config_route():
    try:
        new_config_data = request.json
        cfg = load_config()
        cfg.update(new_config_data)
        if save_config(cfg):
            return jsonify({"success": True, "message": "保存成功，重启软件生效"})
        else:
            return jsonify({"success": False, "message": "保存设置失败，请检查软件是否运行"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app_set.route('/dist/assets/image/<path:filename>')
def serve_logo_image(filename):
    return send_from_directory("dist/assets/image", filename)


def run_settings_web():
    app_set.run(port=5250, host='0.0.0.0')


Thread(target=run_settings_web).start()
default_config = {
    "AI助手名称": "小月",
    "AI助手提示词": "你是专属于开拓者的全能型助手，名称为小月。\n\n回复不要包含emoji，尽量不要超过100字。",
    "用户名": "开拓者", "VITS-ONNX模型名": "sherpa-onnx-vits-zh-ll", "PaddleTTS语速": 5, "PaddleTTS语言": "中文",
    "对话网页端口": 5260, "L2D角色网页端口": 5261, "MMD角色网页端口": 5262, "VRM角色网页端口": 5263,
    "AnythingLLM工作区": "aivm", "思维链think过滤": "开启", "AnythingLLM密钥": "在AnythingLLM获取",
    "Ollama大语言模型": "frob/qwen3.5-instruct:4b", "流式语音合成开关": "关闭",
    "自定义API-LLM-base_url": "填入服务提供方地址，例如 https://api.siliconflow.cn/v1",
    "自定义API-LLM-api_key": "", "自定义API-LLM-model": "填入服务提供方支持的LLM名称，例如 Qwen/Qwen3.5-4B",
    "自定义API-VLM-base_url": "填入服务提供方地址，例如 https://api.siliconflow.cn/v1",
    "自定义API-VLM-api_key": "", "自定义API-VLM-model": "填入服务提供方支持的VLM名称，例如 Qwen/Qwen3.5-4B",
    "实时语音开关键": "x", "桌面宠物置顶": "开启", "Ollama多模态VLM": "frob/qwen3.5-instruct:4b",
    "自定义语音唤醒词": "你好",
    "桌宠位置x": 150, "桌宠位置y": 70, "实时语音打断": "关闭", "语音识别灵敏度": "中", "默认天气城市": "杭州",
    "Dify知识库IP": "127.0.0.1", "Dify知识库密钥": "app-xxxxxxxxxx",
    "edge-tts音色": "晓艺-年轻女声", "edge-tts语速": 0, "edge-tts音高": 10,
    "图像生成引擎": "云端CogView-3-Flash", "声纹识别": "关闭", "摄像头编号": 0, "麦克风编号": 0, "声纹识别阈值": 0.6,
    "Ollama端口": 11434, "LM Studio端口": 1234, "KoboldCpp端口": 5001, "llama.cpp端口": 8080, "本地SD AI绘画端口": 7860,
    "Transformers端口": 8000, "Transformers模型": "model/Qwen3-0.6B", "MMD 3D动作音乐开关(可选项:开启/关闭)": "开启",
    "MMD 3D动作音乐名称(位于data/music_vmd文件夹)": "测试音乐.mp3",
    "GPT-SoVITS端口": 9880, "GPT-SoVITS参考音频文本": "你好，我是小月，很高兴遇见你。有什么我可以帮助你的吗",
    "GPT-SoVITS参考音频路径(位于GSV整合包内)": "example.wav", "GPT-SoVITS参考音频语言": "zh",
    "GPT-SoVITS合成输出语言": "zh", "桌宠悬浮字幕开关(可选项:开启/关闭)": "开启",
    "记忆模式": "中期记忆", "Home Assistant服务器地址": "127.0.0.1:8123",
    "灯类HA实体ID(按钮)": "button.yeelink_cn_xxxxxxxxx_lamp4_toggle_a_2_1",
    "风扇类HA实体ID(按钮)": "button.dmaker_cn_xxxxxxxxx_p8_toggle_a_2_1",
    "插座类HA实体ID(按钮)": "button.cuco_cn_xxxxxxxxx_v3_toggle_a_2_1",
    "HA长期访问令牌": "xxxx.xxxx.xxxx-xxxx", "自定义TTS地址base_url": "https://api.siliconflow.cn/v1/",
    "自定义TTS模型model": "FunAudioLLM/CosyVoice2-0.5B", "自定义TTS语音voice": "FunAudioLLM/CosyVoice2-0.5B:anna",
    "自定义TTS密钥api_key": "", "本地LLM服务器IP": "127.0.0.1", "本地VLM服务器IP": "127.0.0.1",
    "本地TTS服务器IP": "127.0.0.1", "本地AI绘画服务器IP": "127.0.0.1",
    "ZipVoice参考音频路径": "data/model/TTS_ZipVoice/example.wav",
    "ZipVoice参考音频文本": "你好，我是小月，很高兴遇见你。有什么我可以帮助你的吗",
    "摄像头权限": "开启", "音频事件检测开关": "关闭", "音频事件检测阈值": 0.5,
    "自主操控Pro地址": "https://api-inference.modelscope.cn/v1",
    "自主操控Pro视觉模型": "Qwen/Qwen3-VL-30B-A3B-Instruct", "自主操控Pro密钥": "", "IM运行模式权限": "仅聊天(推荐)",
    "飞书机器人开关": "关闭", "飞书机器人AppID": "cli_xxxxxxxxxx", "飞书机器人AppSecret": "",
    "钉钉机器人开关": "关闭", "钉钉机器人ClientID": "dingxxxxxxxxxx", "钉钉机器人ClientSecret": "",
    "QQ机器人开关": "关闭", "QQ机器人AppID": "xxxxxxxxxx", "QQ机器人AppSecret": "",
    "语音合成输入模式": "声音设计", "OmniVoice声音设计": "女，儿童，极高音调，耳语",
    "VoxCPM声音设计": "年轻二次元少女，声音温柔体贴", "OpenClaw网关地址": "http://127.0.0.1:18789",
    "OpenClaw API Key": "xxxxxxxxxx", "OpenClaw模型": "openclaw",
    "OpenClaw提示词": "你是OpenClaw(龙虾)超级智能体，名称为小月", "MQTT开关": "关闭", "MQTT Broker IP": "127.0.0.1",
    "MQTT端口": 1883, "MQTT服务质量": 2, "MQTT订阅主题": "client/qwenpaw", "MQTT发布主题": "server/qwenpaw",
    "GLM智谱BigModel开放平台key": "", "SiliconCloud硅基流动平台key": "", "讯飞星火开放平台key": ""}
try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
        config = json.load(file)
except Exception as e1:
    print(f"加载配置失败，使用默认配置: {e1}")
    config = default_config
asst_name = config["AI助手名称"]
prompt = config["AI助手提示词"]
username = config["用户名"]
vits_model_name = config["VITS-ONNX模型名"]
paddle_rate = config["PaddleTTS语速"]
paddle_lang = config["PaddleTTS语言"]
chatweb_port = config["对话网页端口"]
live2d_port = config["L2D角色网页端口"]
mmd_port = config["MMD角色网页端口"]
vrm_port = config["VRM角色网页端口"]
anything_llm_ws = config["AnythingLLM工作区"]
think_filter_switch = config["思维链think过滤"]
anything_llm_key = config["AnythingLLM密钥"]
ollama_model_name = config["Ollama大语言模型"]
stream_tts_switch = config["流式语音合成开关"]
custom_llm_url = config["自定义API-LLM-base_url"]
custom_llm_key = config["自定义API-LLM-api_key"]
custom_llm_model = config["自定义API-LLM-model"]
custom_vlm_url = config["自定义API-VLM-base_url"]
custom_vlm_key = config["自定义API-VLM-api_key"]
custom_vlm_model = config["自定义API-VLM-model"]
voice_key = config["实时语音开关键"]
pet_top_switch = config["桌面宠物置顶"]
ollama_vlm_name = config["Ollama多模态VLM"]
wake_word = config["自定义语音唤醒词"]
pet_x = int(config["桌宠位置x"])
pet_y = int(config["桌宠位置y"])
voice_break = config["实时语音打断"]
asr_sensitivity = config["语音识别灵敏度"]
weather_city = config["默认天气城市"]
dify_ip = config["Dify知识库IP"]
dify_key = config["Dify知识库密钥"]
edge_speaker = config["edge-tts音色"]
edge_rate = config["edge-tts语速"]
edge_pitch = config["edge-tts音高"]
prefer_draw = config["图像生成引擎"]
voiceprint_switch = config["声纹识别"]
cam_num = int(config["摄像头编号"])
mic_num = int(config["麦克风编号"])
ollama_port = config["Ollama端口"]
lmstudio_port = config["LM Studio端口"]
kobold_port = config["KoboldCpp端口"]
llamacpp_port = config["llama.cpp端口"]
sd_port = config["本地SD AI绘画端口"]
tf_port = config["Transformers端口"]
tf_model = config["Transformers模型"]
vmd_music_switch = config["MMD 3D动作音乐开关(可选项:开启/关闭)"]
vmd_music_name = config["MMD 3D动作音乐名称(位于data/music_vmd文件夹)"]
gsv_prompt = config["GPT-SoVITS参考音频文本"]
gsv_ref_audio_path = config["GPT-SoVITS参考音频路径(位于GSV整合包内)"]
gsv_prompt_lang = config["GPT-SoVITS参考音频语言"]
gsv_lang = config["GPT-SoVITS合成输出语言"]
gsv_port = config["GPT-SoVITS端口"]
pet_subtitle_switch = config["桌宠悬浮字幕开关(可选项:开启/关闭)"]
memory_mode = config["记忆模式"]
ha_api = config["Home Assistant服务器地址"]
entity_id_lamp = config["灯类HA实体ID(按钮)"]
entity_id_fan = config["风扇类HA实体ID(按钮)"]
entity_id_plug = config["插座类HA实体ID(按钮)"]
ha_key = config["HA长期访问令牌"]
custom_tts_url = config["自定义TTS地址base_url"]
custom_tts_model = config["自定义TTS模型model"]
custom_tts_voice = config["自定义TTS语音voice"]
custom_tts_key = config["自定义TTS密钥api_key"]
local_llm_ip = config["本地LLM服务器IP"]
local_vlm_ip = config["本地VLM服务器IP"]
local_tts_ip = config["本地TTS服务器IP"]
local_draw_ip = config["本地AI绘画服务器IP"]
zipvoice_prompt_audio = config["ZipVoice参考音频路径"]
zipvoice_prompt_text = config["ZipVoice参考音频文本"]
cam_permission = config["摄像头权限"]
sound_sense_switch = config["音频事件检测开关"]
sound_sense_threshold = float(config["音频事件检测阈值"])
agi_pc_pro_base_url = config["自主操控Pro地址"]
agi_pc_pro_vlm_model = config["自主操控Pro视觉模型"]
agi_pc_pro_api_key = config["自主操控Pro密钥"]
im_run_mode_permission = config["IM运行模式权限"]
feishu_switch = config["飞书机器人开关"]
feishu_app_id = config["飞书机器人AppID"]
feishu_app_secret = config["飞书机器人AppSecret"]
dingding_switch = config["钉钉机器人开关"]
dingding_client_id = config["钉钉机器人ClientID"]
dingding_client_secret = config["钉钉机器人ClientSecret"]
qq_switch = config["QQ机器人开关"]
qq_app_id = str(config["QQ机器人AppID"])
qq_app_secret = config["QQ机器人AppSecret"]
tts_input_mode = config["语音合成输入模式"]
omnivoice_design_text = config["OmniVoice声音设计"]
voxcpm_design_text = config["VoxCPM声音设计"]
openclaw_gateway = config["OpenClaw网关地址"]
openclaw_api_key = config["OpenClaw API Key"]
openclaw_model = config["OpenClaw模型"]
openclaw_prompt = config["OpenClaw提示词"]
mqtt_switch = config["MQTT开关"]
mq_host = config["MQTT Broker IP"]
mq_port = config["MQTT端口"]
mq_qos = config["MQTT服务质量"]
mq_sub_topic = config["MQTT订阅主题"]
mq_pub_topic = config["MQTT发布主题"]
glm_key = config["GLM智谱BigModel开放平台key"]
sf_key = config["SiliconCloud硅基流动平台key"]
xf_key = config["讯飞星火开放平台key"]
try:
    with open('data/db/preference.json', 'r', encoding='utf-8') as file:
        preference = json.load(file)
    voice_switch = preference["语音识别模式"]
    prefer_llm = preference["对话语言模型"]
    prefer_tts = preference["语音合成引擎"]
    prefer_img = preference["图像识别引擎"]
    ase_switch = preference["主动感知对话"]
    prefer_mode = preference["运行模式切换"]
except:
    voice_switch = "关闭语音识别"
    prefer_llm = "GLM-4.7-Flash"
    prefer_tts = "内置低延迟VITS"
    prefer_img = "GLM-4.6V-Flash"
    ase_switch = "不主动"
    prefer_mode = "提示词对话"
with open('data/db/history.db', 'r', encoding='utf-8') as file:
    history = file.read()
with open('data/db/vrm_model_name.db', 'r', encoding='utf-8') as file:
    vrm_model_name = file.read()
with open('dist/assets/live2d_core/live2d_js_part1', 'r', encoding='utf-8') as file:
    live2d_js_part1 = file.read()
with open('dist/assets/live2d_core/live2d_js_part2', 'r', encoding='utf-8') as file:
    live2d_js_part2 = file.read()
with open('dist/assets/live2d_core/live2d_js_part3', 'r', encoding='utf-8') as file:
    live2d_js_part3 = file.read()
with open('dist/assets/live2d_core/live2d_js_part4', 'r', encoding='utf-8') as file:
    live2d_js_part4 = file.read()
with open('dist/assets/live2d_core/live2d_js_part5', 'r', encoding='utf-8') as file:
    live2d_js_part5 = file.read()
with open('dist/assets/mmd_core/mmd_js_part1', 'r', encoding='utf-8') as file:
    mmd_js_part1 = file.read()
with open('dist/assets/mmd_core/mmd_js_part2', 'r', encoding='utf-8') as file:
    mmd_js_part2 = file.read()
with open('dist/assets/mmd_core/mmd_js_part3', 'r', encoding='utf-8') as file:
    mmd_js_part3 = file.read()
with open('dist/assets/mmd_core/mmd_js_part4', 'r', encoding='utf-8') as file:
    mmd_js_part4 = file.read()
with open('dist/assets/mmd_core/mmd_vmd_js_part1', 'r', encoding='utf-8') as file:
    mmd_vmd_js_part1 = file.read()
with open('dist/assets/mmd_core/mmd_vmd_js_part2', 'r', encoding='utf-8') as file:
    mmd_vmd_js_part2 = file.read()
with open('dist/assets/mmd_core/mmd_vmd_js_part3', 'r', encoding='utf-8') as file:
    mmd_vmd_js_part3 = file.read()


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('119.29.29.29', 1))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    return ip


def upload_image():
    file_path = fd.askopenfilename(title="选择一张JPG图片", filetypes=[("JPG文件", "*.jpg")])
    if file_path:
        target_path = "dist/assets/image/bg.jpg"
        shutil.copy(file_path, target_path)
        messagebox.showinfo("提示", "更换网页背景成功,请刷新网页")


def get_dpi():
    try:  # Windows系统下获取DPI
        hDC = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hDC, 88)
        ctypes.windll.user32.ReleaseDC(0, hDC)
        return dpi
    except:  # 如果获取DPI失败，默认返回96
        return 96


server_ip = get_local_ip()
del_history_alarm = f"您确定要清空{asst_name}的聊天记录吗？\n如有需要可先点击右下角🔼导出记录再清除\n(本功能不影响AI助手的记忆)"
del_memory_alarm = f"您确定要删除{asst_name}的记忆吗？\n确定后需立即重启软件生效\n(本功能不会清空聊天记录)"
mzw_model_url = "https://www.aplaybox.com/model/model"
mode_options = ["提示词对话", "多智能体助手", "自主操控Lite", "自主操控Pro", 'OpenClaw龙虾', 'MQTT/QwenPaw']
voice_options = ["实时语音识别", "自定义唤醒词", "关闭语音识别"]
llm_options = ["GLM-4.7-Flash", "千问Qwen3-8B", "千问Qwen3.5-4B", "DeepSeek-R1-8B", "星火Lite", "本地Ollama LLM",
               "本地LM Studio", "本地KoboldCpp", "本地llama.cpp", "本地Transformers", "Dify聊天助手", "AnythingLLM",
               "自定义API-LLM"]
tts_options = ["内置低延迟VITS", "内置ZipVoice", "云端edge-tts", "云端Paddle-TTS", "本地GPT-SoVITS", "本地OmniVoice",
               "本地VoxCPM", "本地Qwen-TTS", "本地Index-TTS", "系统自带TTS", "自定义API-TTS", "关闭语音合成"]
img_options = ["GLM-4.6V-Flash", "千问Qwen3.5-4B", "本地Ollama VLM", "本地LM Studio", "本地KoboldCpp", "本地llama.cpp",
               "自定义API-VLM", "关闭图像识别"]
all_task = "音乐播放、语音输入、打开软件/网页、音量减小、音量增大、文本写作、翻译屏幕内容、解释屏幕内容、总结屏幕内容、续写屏幕内容、屏幕内容问答、摄像头场景问答、灯类智能家居控制、风扇类智能家居控制、插座类智能家居控制、天气查询、热搜新闻、系统状态查询、联网搜索、视频生成、绘画图像生成、网页开发、PPT制作、表格制作、日常闲聊"
glm_llm_model = "glm-4.7-flash"
glm_vlm_model = "glm-4.6v-flash"
sf_url = "https://api.siliconflow.cn/v1"
xf_url = "https://spark-api-open.xf-yun.com/v1"
xf_model = "lite"
model_path = "data/model"
vits_target_dir = f"{model_path}/TTS"
zipvoice_dir = f"{model_path}/TTS_ZipVoice/sherpa-onnx-zipvoice-distill-int8-zh-en-emilia"
