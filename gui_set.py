import time
import wave
import pyaudio
from gui_sub import *


def open_setting_w():
    def open_settings_web():
        time.sleep(1)
        wb.open("http://127.0.0.1:5250")
    def open_voiceprint_manage():
        def record_audio():
            p = pyaudio.PyAudio()
            stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK,
                            input_device_index=mic_num)
            print("开始录音...")
            frames = []
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            print("录音结束")
            stream.stop_stream()
            stream.close()
            p.terminate()
            wf = wave.open(FILE_PATH, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            messagebox.showinfo("成功",
                                f"声纹录制完成\n您可以在软件设置网页中语音识别栏目开启声纹识别\nAI助手将只应答您的语音\n保存重启软件后生效\n(您的声纹文件位于{FILE_PATH})")

        def start_recording():
            if os.path.exists(FILE_PATH):
                result = messagebox.askyesno("确认",
                                             "声纹已存在，是否重新录制？将录制5秒钟音频\n请确保在安静的环境中录制\n点击“是”后，请说“你好，很高兴遇见你，这是我的声音”")
            else:
                result = messagebox.askyesno("确认",
                                             "是否开始录制声纹？将录制5秒钟音频\n请确保在安静的环境中录制\n点击“是”后，请说“你好，很高兴遇见你，这是我的声音”")
            if result:
                record_audio()

        def delete_voiceprint():
            if os.path.exists(FILE_PATH):
                result = messagebox.askyesno("确认", f"是否确认删除声纹文件？\n(您的声纹文件位于{FILE_PATH})")
                if result:
                    try:
                        os.remove(FILE_PATH)
                        messagebox.showinfo("完成", "声纹文件已删除")
                    except Exception as e:
                        messagebox.showerror("错误", f"删除文件时出错，错误详情：{e}")
            else:
                messagebox.showinfo("提示", "没有录制的声纹文件，无需删除")

        FILE_PATH = 'data/cache/voiceprint/myvoice.wav'
        FORMAT = pyaudio.paInt16
        CHANNELS, RATE, CHUNK = 1, 16000, 1024
        RECORD_SECONDS = 5
        voiceprint_manage_w = tk.Toplevel(root)
        voiceprint_manage_w.title("声纹管理 - 枫云AI助手社区版")
        original_window_size4 = (350, 110)
        scaled_window_size4 = scaled_size(original_window_size4)
        voiceprint_manage_w.geometry(f"{scaled_window_size4[0]}x{scaled_window_size4[1]}")
        tk.Button(voiceprint_manage_w, text="开始录制", command=start_recording, bg="green", fg="white").pack(pady=10)
        tk.Button(voiceprint_manage_w, text="删除声纹", command=delete_voiceprint, bg="#FF7700", fg="white").pack(
            pady=10)
        voiceprint_manage_w.iconbitmap("data/image/logo.ico")

    def restore_set():
        if messagebox.askokcancel("恢复默认设置", "您确定要重置枫云AI助手社区版吗？\n记忆、聊天记录不受影响"):
            with open('data/db/config.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=4)
            with open('data/db/init.db', 'w', encoding="utf-8") as f:
                f.write("0")
            with open('data/db/vrm_model_name.db', 'w', encoding="utf-8") as f:
                f.write("小月.vrm")
            with open('dist/assets/live2d_core/live2d_js_set.txt', 'w', encoding='utf-8') as f:
                f.write('[模型路径]\nhiyori_free_t08/hiyori_free_t08.model3.json\n\n')
                f.write(f'[模型横坐标]\n625\n\n')
                f.write('[模型纵坐标]\n-25\n\n')
                f.write('[模型大小]\n15')
            with open('dist/assets/live2d.js', 'w', encoding='utf-8') as f:
                f.write(live2d_js_part1 + "hiyori_free_t08/hiyori_free_t08.model3.json" + live2d_js_part2 + "625"
                        + live2d_js_part3 + "-25" + live2d_js_part4 + "15" + live2d_js_part5)
            with open('dist/assets/mmd_core/mmd_js_set.txt', 'w', encoding='utf-8') as f:
                f.write('[模型路径]\n小月/小月.pmx\n\n')
                f.write('[动作路径]\nexample.vmd\n\n')
                f.write('[模型嘴索引]\n135\n\n')
                f.write('[模型眼索引]\n60')
            with open('dist/assets/mmd.js', 'w', encoding='utf-8') as f:
                f.write(
                    mmd_js_part1 + "小月/小月.pmx" + mmd_js_part2 + "133" + mmd_js_part3 + "60" + mmd_js_part4)
            with open('dist/assets/mmd_vmd.js', 'w', encoding='utf-8') as f:
                f.write(
                    mmd_vmd_js_part1 + "小月/小月.pmx" + mmd_vmd_js_part2 + "example.vmd" + mmd_vmd_js_part3)
            messagebox.showinfo("恢复默认设置成功", "恢复默认设置成功！重启软件生效")
            setting_w.destroy()

    setting_w = tk.Toplevel(root)
    setting_w.title("软件设置面板 - 枫云AI助手社区版")
    original_window_size2 = (500, 200)
    scaled_window_size2 = scaled_size(original_window_size2)
    setting_w.geometry(f"{scaled_window_size2[0]}x{scaled_window_size2[1]}")
    logo_label2 = tk.Label(setting_w, image=logo_photo)
    logo_label2.place(relx=0.275, rely=0.05, anchor='n')
    tk.Button(setting_w, text=" 打开设置网页 ", command=lambda: wb.open("http://127.0.0.1:5250"), bg="green", fg="white").place(relx=0.575,
                                                                                                      rely=0.05)
    tk.Button(setting_w, text="   声纹管理   ", command=open_voiceprint_manage, bg="green", fg="white").place(
        relx=0.125, rely=0.25)
    tk.Button(setting_w, text=" VITS模型管理 ", command=lambda: os.startfile("data\\model\\TTS"), bg="green",
              fg="white").place(relx=0.575, rely=0.25)
    tk.Button(setting_w, text=" 开源项目官网 ", command=lambda: wb.open("https://mewco-ai.github.io/2024/07/09/asstcomm/"), bg="#3E92ED", fg="white").place(
        relx=0.125, rely=0.45)
    tk.Button(setting_w, text="下载本地AI引擎", command=lambda: wb.open("https://mewco-ai.github.io/2024/03/13/engine/"), bg="#3E92ED", fg="white").place(
        relx=0.575, rely=0.45)
    tk.Button(setting_w, text=" ZipVoice管理 ", command=lambda: os.startfile("data\\model\\TTS_ZipVoice"), bg="green", fg="white").place(relx=0.125,
                                                                                                      rely=0.65)
    tk.Button(setting_w, text=" 恢复默认设置 ", command=restore_set, bg="#FF7700", fg="white").place(relx=0.575,
                                                                                                     rely=0.65)
    tk.Label(setting_w, text="*本软件由MewCo-AI Team出品,开源免费,仅供个人研究学习,严禁用于商业用途\n开源项目地址：https://github.com/MewCo-AI/mewco_ai_assistant_comm", font=("楷体", 10), fg="green").place(relx=0.5, rely=0.9, anchor='center')
    setting_w.iconbitmap("data/image/logo.ico")
    Thread(target=open_settings_web).start()
    setting_w.mainloop()
