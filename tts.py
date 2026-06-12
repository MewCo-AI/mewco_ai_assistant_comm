import asyncio
import glob
import edge_tts
import pyttsx3
import sherpa_onnx
import numpy as np
import soundfile as sf
from function import *

vits_model_dir = f"{vits_target_dir}/{vits_model_name}"
vits_tokens_path = f"{vits_model_dir}/tokens.txt"
vits_lexicon_path = f"{vits_model_dir}/lexicon.txt"
vits_dict_dir = f"{vits_model_dir}/dict"
vits_tts = None
try:
    vits_model_path = glob.glob(os.path.join(vits_model_dir, "*.onnx"))[0]
    vits_tts_config = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=vits_model_path, lexicon=vits_lexicon_path,
                                                   tokens=vits_tokens_path, dict_dir=vits_dict_dir), provider="cpu",
        num_threads=int(os.cpu_count()) - 1))
except Exception as e1:
    print(f"VITS模型加载错误，详情：{e1}")
zipvoice_tts = None
zip_tokens_path = f"{zipvoice_dir}/tokens.txt"
zip_encoder_path = f"{zipvoice_dir}/encoder.int8.onnx"
zip_decoder_path = f"{zipvoice_dir}/decoder.int8.onnx"
zip_data_dir_path = f"{zipvoice_dir}/espeak-ng-data"
zip_lexicon_path = f"{zipvoice_dir}/lexicon.txt"
zip_vocoder_path = f"{zipvoice_dir}/vocos_24khz.onnx"
try:
    zipvoice_config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(zipvoice=sherpa_onnx.OfflineTtsZipvoiceModelConfig(
            tokens=zip_tokens_path, encoder=zip_encoder_path, decoder=zip_decoder_path, data_dir=zip_data_dir_path,
            lexicon=zip_lexicon_path, vocoder=zip_vocoder_path, feat_scale=0.1, t_shift=0.5, target_rms=0.1,
            guidance_scale=1.0), provider="cpu", debug=False, num_threads=int(os.cpu_count()) - 1), rule_fsts="",
        max_num_sentences=1)
except Exception as e1:
    print(f"ZipVoice模型加载错误，详情：{e1}")
voice_path = 'data/cache/cache_voice'
lang_mapping = {"中文": "zh", "英语": "uk", "日语": "jp"}
select_lang = lang_mapping.get(paddle_lang, "kor")
edge_speaker_mapping = {"晓艺-年轻女声": "zh-CN-XiaoyiNeural", "晓晓-成稳女声": "zh-CN-XiaoxiaoNeural",
                        "云健-大型纪录片男声": "zh-CN-YunjianNeural", "云希-短视频热门男声": "zh-CN-YunxiNeural",
                        "云夏-年轻男声": "zh-CN-YunxiaNeural", "云扬-成稳男声": "zh-CN-YunyangNeural",
                        "晓北-辽宁话女声": "zh-CN-liaoning-XiaobeiNeural",
                        "晓妮-陕西话女声": "zh-CN-shaanxi-XiaoniNeural", "晓佳-粤语成稳女声": "zh-HK-HiuGaaiNeural",
                        "晓满-粤语年轻女声": "zh-HK-HiuMaanNeural", "云龙-粤语男声": "zh-HK-WanLungNeural",
                        "晓辰-台湾话年轻女声": "zh-TW-HsiaoChenNeural", "晓宇-台湾话成稳女声": "zh-TW-HsiaoYuNeural",
                        "云哲-台湾话男声": "zh-TW-YunJheNeural", "佳太-日语男声": "ja-JP-KeitaNeural"}
edge_select_speaker = edge_speaker_mapping.get(edge_speaker, "ja-JP-NanamiNeural")
play_tts_flag = 0
try:
    x3_engine = pyttsx3.init()
except Exception as e1:
    print(f"pyttsx3初始化错误，详情：{e1}")


def stop_tts():
    global play_tts_flag
    pg.quit()
    play_tts_flag = 0


def tts_vits(text):
    global vits_tts
    if vits_tts is None:
        vits_tts = sherpa_onnx.OfflineTts(vits_tts_config)
    audio = vits_tts.generate(text, sid=0, speed=1.0)
    if vits_model_name == "sherpa-onnx-vits-zh-ll":
        samples = np.array(audio.samples, dtype=np.float32)
        amplified_samples = samples * 4  # 音量放大4倍
        amplified_samples = np.clip(amplified_samples, -1.0, 1.0)
        amplified_samples_int16 = (amplified_samples * 32767).astype(np.int16)
        sf.write(voice_path, amplified_samples_int16, samplerate=audio.sample_rate, subtype="PCM_16", format="wav")
    else:
        sf.write(voice_path, audio.samples, samplerate=audio.sample_rate, subtype="PCM_16", format="wav")


def tts_zipvoice(text):
    def read_wave(wave_filename):
        with wave.open(wave_filename) as f:
            nchannels = f.getnchannels()
            sampwidth = f.getsampwidth()
            framerate = f.getframerate()
            num_samples = f.getnframes()
            frames = f.readframes(num_samples)
            dtype_map = {1: np.uint8, 2: np.int16, 3: np.int32, 4: np.int32}
            dtype = dtype_map[sampwidth]
            if sampwidth == 3:
                samples = np.frombuffer(frames, dtype=np.uint8)
                samples = np.zeros((samples.shape[0] // 3, 4), dtype=np.uint8)
                samples[:, 1:] = frames.reshape(-1, 3)
                samples = samples.view(np.int32).reshape(-1)
            else:
                samples = np.frombuffer(frames, dtype=dtype)
            if nchannels > 1:
                samples = samples.reshape(-1, nchannels)
                samples = np.mean(samples, axis=1)
            samples_float32 = samples.astype(np.float32)
            if sampwidth == 1:
                samples_float32 = (samples_float32 - 128) / 128
            elif sampwidth == 2:
                samples_float32 = samples_float32 / 32768.0
            elif sampwidth in (3, 4):
                max_val = 2 ** (8 * sampwidth - 1)
                samples_float32 = samples_float32 / max_val
            return samples_float32, framerate

    global zipvoice_tts
    if zipvoice_tts is None:
        zipvoice_tts = sherpa_onnx.OfflineTts(zipvoice_config)
    prompt_samples, sample_rate = read_wave(zipvoice_prompt_audio)
    audio = zipvoice_tts.generate(text, zipvoice_prompt_text, prompt_samples, sample_rate, speed=1, num_steps=4)
    sf.write(voice_path, audio.samples, samplerate=audio.sample_rate, subtype="PCM_16", format="wav")


def custom_tts(text):
    client = OpenAI(api_key=custom_tts_key, base_url=custom_tts_url)
    with client.audio.speech.with_streaming_response.create(
            model=custom_tts_model, voice=custom_tts_voice, input=text, response_format="mp3") as response:
        response.stream_to_file(voice_path)


def get_tts_play(text):
    global play_tts_flag
    play_tts_flag = 1

    def play_voice():
        pg.mixer.init()
        try:
            pg.mixer.music.load(voice_path)
            pg.mixer.music.play()
            while pg.mixer.music.get_busy() and play_tts_flag == 1:
                pg.time.Clock().tick(1)
            pg.mixer.music.stop()
        except:
            pass
        pg.quit()

    def split_text(text2):
        segments2 = re.split(r'([\n:：!！?？;；。])', text2)
        combined = []
        for i in range(0, len(segments2), 2):
            if i + 1 < len(segments2):
                combined.append(segments2[i] + segments2[i + 1])
            elif segments2[i].strip():  # 处理最后可能剩余的文本部分
                combined.append(segments2[i])
        return [seg.strip() for seg in combined if seg.strip()]  # 过滤掉空字符串的分段

    async def ms_edge_tts(segment2):
        if edge_rate >= 0:
            edge_rate2 = "+" + str(edge_rate)
        else:
            edge_rate2 = str(edge_rate)
        if edge_pitch >= 0:
            edge_pitch2 = "+" + str(edge_pitch)
        else:
            edge_pitch2 = str(edge_pitch)
        communicate = edge_tts.Communicate(segment2, edge_select_speaker, rate=f"{edge_rate2}%",
                                           pitch=f"{edge_pitch2}Hz")
        await communicate.save(voice_path)

    processed_text = text.split("</think>")[-1].strip().replace("#", "").replace("*", "")
    processed_text = re.sub(r'[(（].*?[)）]', '', processed_text)
    if stream_tts_switch == "开启":
        segments = split_text(processed_text)
        if not segments:  # 如果切片后为空，使用原始文本
            segments = [processed_text]
    else:
        segments = [processed_text]  # 不切片，直接使用完整文本

    def get_tts_play_th():
        error_messages = {"Error opening", "Permission denied"}
        try:
            for segment in segments:
                if play_tts_flag != 1:
                    break
                if tts_menu.get() == "云端edge-tts":
                    asyncio.run(ms_edge_tts(segment))
                    play_voice()
                elif tts_menu.get() == "云端Paddle-TTS":
                    url = f'https://fanyi.baidu.com/gettts?lan={select_lang}&spd={paddle_rate}&text={segment}'
                    res = rq.get(url)
                    with open(voice_path, 'wb') as f:
                        f.write(res.content)
                    play_voice()
                elif tts_menu.get() == "本地GPT-SoVITS":
                    url = f'http://{local_tts_ip}:{gsv_port}/tts?text={segment}&text_lang={gsv_lang}&prompt_text={gsv_prompt}&prompt_lang={gsv_prompt_lang}&ref_audio_path={gsv_ref_audio_path}'
                    try:
                        res = rq.get(url)
                        with open(voice_path, 'wb') as f:
                            f.write(res.content)
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice(f"本地GPT-SoVITS整合包API服务器未开启，错误详情：{e}")
                elif tts_menu.get() == "本地OmniVoice":
                    url_clone = f'http://{local_tts_ip}:9881/omnivoice_clone/?text={segment}'
                    url_design = f'http://{local_tts_ip}:9881/omnivoice_design/?text={segment}&instruct={omnivoice_design_text}'
                    try:
                        if tts_input_mode == "声音克隆":
                            res = rq.get(url_clone)
                        else:
                            res = rq.get(url_design)
                        with open(voice_path, 'wb') as f:
                            f.write(res.content)
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice(f"本地OmniVoice整合包API服务器未开启，错误详情：{e}")
                elif tts_menu.get() == "本地Qwen-TTS":
                    url = f'http://{local_tts_ip}:9882/qwen_tts/?text={segment}'
                    try:
                        res = rq.get(url)
                        with open(voice_path, 'wb') as f:
                            f.write(res.content)
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice(f"本地Qwen-TTS整合包API服务器未开启，错误详情：{e}")
                elif tts_menu.get() == "本地Index-TTS":
                    url = f'http://{local_tts_ip}:9884/indextts/?text={segment}'
                    try:
                        res = rq.get(url)
                        with open(voice_path, 'wb') as f:
                            f.write(res.content)
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice(f"本地Index-TTS整合包API服务器未开启，错误详情：{e}")
                elif tts_menu.get() == "本地VoxCPM":
                    url_clone = f'http://{local_tts_ip}:9885/voxcpm/?text={segment}'
                    url_design = f'http://{local_tts_ip}:9885/voxcpm_design/?text={segment}&instruct={voxcpm_design_text}'
                    try:
                        if tts_input_mode == "声音克隆":
                            res = rq.get(url_clone)
                        else:
                            res = rq.get(url_design)
                        with open(voice_path, 'wb') as f:
                            f.write(res.content)
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice(f"本地VoxCPM整合包API服务器未开启，错误详情：{e}")
                elif tts_menu.get() == "系统自带TTS":
                    try:
                        x3_engine.save_to_file(segment, voice_path)
                        x3_engine.runAndWait()
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice("您的电脑未启用系统自带TTS，可选择其他语音合成引擎")
                elif tts_menu.get() == "内置低延迟VITS":
                    try:
                        tts_vits(segment)
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice(f"内置低延迟VITS服务拥挤，详情：{e}")
                elif tts_menu.get() == "内置ZipVoice":
                    try:
                        tts_zipvoice(segment)
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice(f"内置ZipVoice服务拥挤，详情：{e}")
                elif tts_menu.get() == "自定义API-TTS":
                    try:
                        custom_tts(segment)
                        play_voice()
                    except Exception as e:
                        if not any(msg in str(e) for msg in error_messages):
                            notice(f"请前往data/set/custom_tts_set.txt正确配置自定义API-TTS，错误详情：{e}")
        except Exception as e:
            if not any(msg in str(e) for msg in error_messages):
                notice(f"{tts_menu.get()}服务拥挤或出错，可选择其他语音合成引擎，错误：{str(e)}")

    Thread(target=get_tts_play_th).start()
