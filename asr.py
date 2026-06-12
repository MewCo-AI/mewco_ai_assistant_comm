import json
import os
import wave
import pyaudio
import sherpa_onnx
import numpy as np
import soundfile as sf

model_path = "data/model"
asr_model_path = f"{model_path}/ASR/sherpa-onnx-sense-voice-zh-en-ja-ko-yue"
vp_model_path = f"{model_path}/SpeakerID/3dspeaker_speech_campplus_sv_zh_en_16k-common_advanced.onnx"
audio_tag_model_path = f"{model_path}/AudioTag/sherpa-onnx-zipformer-small-audio-tagging"
vp_config, extractor, audio1, sample_rate1, embedding1, audio_tagger = None, None, None, None, None, None
with open('data/db/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
asr_sensitivity = config["语音识别灵敏度"]
voiceprint_switch = config["声纹识别"]
mic_num = int(config["麦克风编号"])
voiceprint_threshold = float(config["声纹识别阈值"])
sound_sense_switch = config["音频事件检测开关"]
sound_sense_threshold = float(config["音频事件检测阈值"])
SILENCE_DURATION_MAP = {"高": 1, "中": 2, "低": 3}
SILENCE_DURATION = SILENCE_DURATION_MAP.get(asr_sensitivity, 3)
FORMAT = pyaudio.paInt16
CHANNELS, RATE, CHUNK = 1, 16000, 1024
SILENCE_CHUNKS = SILENCE_DURATION * RATE / CHUNK  # 静音持续的帧数
p, stream, recognizer = None, None, None
cache_path = "data/cache/cache_record.wav"
model = f"{asr_model_path}/model.int8.onnx"
tokens = f"{asr_model_path}/tokens.txt"
audio_event_mapping = {
    # 人声/人体发出的声音
    "Sneeze": "[打喷嚏]", "Throat clearing": "[清嗓子]", "Cough": "[咳嗽]", "cry": "[哭泣]", "Laughter": "[笑声]",
    "Snort": "[呼吸声]", "Finger snapping": "[响指声]", "Clapping": "[鼓掌]", "Applause": "[掌声]", "Sigh": "[叹气声]",
    "Hiccup": "[打嗝声]", "Chewing": "[咀嚼声]", "Whistling": "[吹口哨]", "Whistle": "[吹口哨]", "Snoring": "[打鼾声]",
    # 动物叫声
    "Meow": "[猫叫声]", "Dog": "[狗叫声]", "Crowing": "[鸡叫声]", "Chicken": "[鸡叫声]", "Quack": "[鸭叫声]",
    "Goose": "[鹅叫声]", "Honk": "[鹅叫声]", "Sheep": "[羊叫声]", "Bleat": "[羊叫声]", "Bee": "[蜜蜂声]",
    "Cattle": "[牛叫声]", "Moo": "[牛叫声]", "Oink": "[猪叫声]", "Neigh": "[马叫声]", "Frog": "[青蛙声]",
    "Cricket": "[蟋蟀声]", "Howl": "[狼嚎声]", "housefly": "[苍蝇声]", "Insect": "[昆虫声]",
    # 家居/日常物品声音
    "Knock": "[敲击声]", "Ding": "[手机通知声]", "Ringtone": "[手机铃声]", "Doorbell": "[门铃声]", "Door": "[开门声]",
    "Dishes": "[餐具声]", "Alarm clock": "[闹钟声]",
    # 交通工具/环境声音
    "Vehicle horn": "[喇叭声]", "Bicycle bell": "[自行车铃铛声]", "Vehicle": "[车辆声]", "Helicopter": "[直升机声]",
    "Fireworks": "[烟花声]", "Explosion": "[爆破声]", "Stream": "[水流声]"}


def init_audio_tagger():  # 初始化音频标签检测器
    global audio_tagger
    if audio_tagger is None:
        try:
            model_file = f"{audio_tag_model_path}/model.int8.onnx"
            label_file = f"{audio_tag_model_path}/class_labels_indices.csv"
            at_config = sherpa_onnx.AudioTaggingConfig(
                model=sherpa_onnx.AudioTaggingModelConfig(
                    zipformer=sherpa_onnx.OfflineZipformerAudioTaggingModelConfig(
                        model=model_file), num_threads=os.cpu_count(), debug=False, provider="cpu"),
                labels=label_file, top_k=5)
            audio_tagger = sherpa_onnx.AudioTagging(at_config)
        except Exception as e1:
            print(f"音频事件检测模型加载失败: {e1}")
            return False
    return True


def detect_audio_event(audio_path):  # 检测音频中的事件
    global audio_tagger
    if not init_audio_tagger():
        return ""
    try:
        data, sample_rate = sf.read(audio_path, dtype="float32", always_2d=True)
        if len(data.shape) > 1:
            data = data[:, 0]
        audio_stream = audio_tagger.create_stream()
        audio_stream.accept_waveform(sample_rate=sample_rate, waveform=data)
        results = audio_tagger.compute(audio_stream)
        if results and len(results) > 0:
            top_event = results[0]
            if top_event.prob > sound_sense_threshold:
                for key, value in audio_event_mapping.items():
                    if key in top_event.name:
                        return value
        return ""
    except Exception as e1:
        print(f"音频事件检测出错: {e1}")
        return ""


def rms(data):  # 计算音频数据的均方根
    return np.sqrt(np.mean(np.frombuffer(data, dtype=np.int16) ** 2))


def dbfs(rms_value):  # 将均方根转换为分贝满量程（dBFS）
    return 20 * np.log10(rms_value / (2 ** 15))  # 16位音频


def record_audio():
    global p, stream
    frames = []
    recording = True
    silence_counter = 0  # 用于记录静音持续的帧数
    if p is None:
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK,
                        input_device_index=mic_num)
    while recording:
        data = stream.read(CHUNK)
        frames.append(data)
        current_rms = rms(data)
        current_dbfs = dbfs(current_rms)
        if str(current_dbfs) != "nan":
            silence_counter += 1  # 增加静音计数
            if silence_counter > SILENCE_CHUNKS:  # 判断是否达到设定的静音持续时间
                recording = False
        else:
            silence_counter = 0  # 重置静音计数
    return b''.join(frames)


def verify_speakers():
    global vp_config, extractor, audio1, sample_rate1, embedding1
    audio_file1 = "data/cache/voiceprint/myvoice.wav"
    audio_file2 = cache_path

    def load_audio(filename):
        audio, sample_rate = sf.read(filename, dtype="float32", always_2d=True)
        audio = audio[:, 0]
        return audio, sample_rate

    def extract_speaker_embedding(audio, sample_rate):
        vp_stream = extractor.create_stream()
        vp_stream.accept_waveform(sample_rate=sample_rate, waveform=audio)
        vp_stream.input_finished()
        embedding = extractor.compute(vp_stream)
        return np.array(embedding)

    def cosine_similarity():
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        return dot_product / (norm1 * norm2) if (norm1 * norm2) != 0 else 0.0

    print("正在加载说话人嵌入模型...")
    try:
        if vp_config is None:
            vp_config = sherpa_onnx.SpeakerEmbeddingExtractorConfig(model=vp_model_path, debug=False, provider="cpu",
                                                                    num_threads=int(os.cpu_count()) - 1)
            extractor = sherpa_onnx.SpeakerEmbeddingExtractor(vp_config)
            audio1, sample_rate1 = load_audio(audio_file1)
            embedding1 = extract_speaker_embedding(audio1, sample_rate1)
        audio2, sample_rate2 = load_audio(audio_file2)
        embedding2 = extract_speaker_embedding(audio2, sample_rate2)
        similarity = cosine_similarity()
        if similarity >= voiceprint_threshold:
            print(f"✓ 结果: 是同一个说话人 (相似度 {similarity:.4f} >= 阈值 {voiceprint_threshold})")
            return True
        else:
            print(f"✗ 结果: 不是同一个说话人 (相似度 {similarity:.4f} < 阈值 {voiceprint_threshold})")
            return False
    except Exception as e:
        print(f"声纹识别出错，详情：{e}")
        return True


def recognize_audio(audiodata):  # 保存录音到临时文件
    global recognizer
    if recognizer is None:
        recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(model=model, tokens=tokens, use_itn=True,
                                                                    num_threads=int(os.cpu_count()) - 1)
    with wave.open(cache_path, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(audiodata)
    with wave.open(cache_path, 'rb') as wf:
        n_frames = wf.getnframes()
        duration = n_frames / RATE
    sound_tag = ""
    if sound_sense_switch == "开启":
        sound_tag = detect_audio_event(cache_path)
    if duration < SILENCE_DURATION + 0.5:
        return sound_tag
    if voiceprint_switch == "开启":
        if not verify_speakers():
            return ""
    audio, sample_rate = sf.read(cache_path, dtype="float32", always_2d=True)
    asr_stream = recognizer.create_stream()
    asr_stream.accept_waveform(sample_rate, audio[:, 0])
    recognizer.decode_stream(asr_stream)
    res = json.loads(str(asr_stream.result))
    emotion_key = res.get('emotion', '').strip('<|>')
    event_key = res.get('event', '').strip('<|>')
    text = res.get('text', '')
    emotion_dict = {"HAPPY": "[开心]", "SAD": "[伤心]", "ANGRY": "[愤怒]", "DISGUSTED": "[厌恶]", "SURPRISED": "[惊讶]",
                    "NEUTRAL": "", "EMO_UNKNOWN": ""}
    event_dict = {"BGM": "", "Applause": "[鼓掌]", "Laughter": "[大笑]", "Cry": "[哭]", "Sneeze": "[打喷嚏]",
                  "Cough": "[咳嗽]", "Breath": "[深呼吸]", "Speech": "", "Event_UNK": ""}
    emotion = emotion_dict.get(emotion_key, "")
    event = event_dict.get(event_key, "")
    result = sound_tag + event + text + emotion
    if result == "The.":
        return ""
    return result
