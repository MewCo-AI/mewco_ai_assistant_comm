from PIL import ImageDraw
from live2d import run_live2d
from mmd import run_mmd
from im_bot import *
from vrm import *


def refresh_preference():
    while True:
        try:
            new_preference = {"语音识别模式": asr_menu.get(), "对话语言模型": llm_menu.get(),
                              "语音合成引擎": tts_menu.get(), "图像识别引擎": img_menu.get(),
                              "主动感知对话": ase_menu.get(), "运行模式切换": mode_menu.get()}
            with open('data/db/preference.json', 'w', encoding='utf-8') as f:
                json.dump(new_preference, f, ensure_ascii=False, indent=4)
            with open(f'data/db/history.db', 'w', encoding='utf-8') as f:
                f.write(output_box.get(1.0, "end").strip() + "\n")
        except:
            print("用户偏好保存错误")
        time.sleep(0.1)


def text_chat(event=None):
    def text_chat_th():
        stop_tts()
        msg = input_box.get("1.0", "end").strip()
        if asr_menu.get() == "实时语音识别" and tts_menu.get() != "关闭语音合成":
            messagebox.showinfo("提示", "请关闭实时语音识别或关闭语音合成后\n再打字发送")
            return
        if msg == "":
            messagebox.showinfo("提示", "请输入内容后再发送")
            return
        input_box.delete("1.0", "end")
        common_chat(msg)

    Thread(target=text_chat_th).start()


def sense_voice_th():  # 语音识别(普通模式)
    from asr import recognize_audio, record_audio
    while True:
        try:
            if asr_menu.get() == "实时语音识别" or asr_menu.get() == "自定义唤醒词":
                pg.mixer.init()
                if pg.mixer.music.get_busy():
                    time.sleep(0.1)
                else:
                    say_text = recognize_audio(record_audio())
                    if len(say_text) > 1 and asr_menu.get() == "实时语音识别":
                        common_chat(say_text)
                    elif wake_word in say_text and asr_menu.get() == "自定义唤醒词":
                        if len(say_text) > 2:
                            say_text = say_text.replace(wake_word + "，", "").replace(wake_word, "")
                        common_chat(say_text)
            else:
                time.sleep(0.1)
        except:
            time.sleep(0.1)


def sense_voice_th_break():  # 语音识别(实时语音打断模式)
    from asr import recognize_audio, record_audio
    while True:
        try:
            if asr_menu.get() == "实时语音识别" or asr_menu.get() == "自定义唤醒词":
                say_text = recognize_audio(record_audio())
                if len(say_text) > 1 and asr_menu.get() == "实时语音识别":
                    stop_tts()
                    common_chat(say_text)
                elif wake_word in say_text and asr_menu.get() == "自定义唤醒词":
                    if len(say_text) > 2:
                        say_text = say_text.replace(wake_word + "，", "").replace(wake_word, "")
                    stop_tts()
                    common_chat(say_text)
            else:
                time.sleep(0.1)
        except:
            time.sleep(0.1)


def switch_voice(event=None):
    if asr_menu.get() == "实时语音识别":
        voice_var.set("关闭语音识别")
    elif asr_menu.get() == "关闭语音识别":
        voice_var.set("实时语音识别")


def switch_float_ball():
    def show_menu_fb(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def on_left_button_press(event):
        global _start_x, _start_y, _window_x, _window_y
        _start_x = event.x_root
        _start_y = event.y_root
        _window_x = float_ball_w.winfo_x()
        _window_y = float_ball_w.winfo_y()

    def on_mouse_move(event):
        global _window_x, _window_y
        dx = event.x_root - _start_x
        dy = event.y_root - _start_y
        new_x = _window_x + dx
        new_y = _window_y + dy
        float_ball_w.geometry(f"+{new_x}+{new_y}")

    def switch_back_window():
        float_ball_w.destroy()
        root.deiconify()

    def create_circular_image(image_path, size):
        try:
            img = Image.open(image_path).convert("RGBA")
        except:
            img = Image.open("data/image/logo.png").convert("RGBA")
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        if img.width != img.height:
            min_side = min(img.width, img.height)
            left = (img.width - min_side) // 2
            top = (img.height - min_side) // 2
            right = left + min_side
            bottom = top + min_side
            img = img.crop((left, top, right, bottom))
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        mask = Image.new("L", (size, size), 0)  # L模式：8位灰度图，0为全黑（透明）
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)  # 绘制白色圆形（不透明）
        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))  # 透明背景
        result.paste(img, (0, 0), mask=mask)  # 把原图贴到透明背景上，用mask控制显示区域
        return ImageTk.PhotoImage(result)

    root.withdraw()
    float_ball_w = tk.Toplevel(root)
    float_ball_w.attributes('-topmost', True)  # 置顶
    float_ball_w.overrideredirect(True)  # 去除窗口边框
    float_ball_w.attributes('-transparentcolor', 'black')  # 设置黑色为透明色（兜底）
    float_ball_w.config(bg='black')
    float_ball_w.iconbitmap('data/image/logo.ico')
    try:
        photo = create_circular_image(f"data/image/ch/{asst_name}.png", FT_WINDOW_SIZE)
    except:
        photo = create_circular_image("data/image/logo.png", FT_WINDOW_SIZE)
    label = tk.Label(float_ball_w, image=photo, bg='black')
    label.pack()
    label.photo = photo
    x = (float_ball_w.winfo_screenwidth() // 2) - (FT_WINDOW_SIZE // 2)
    y = (float_ball_w.winfo_screenheight() // 2) - (FT_WINDOW_SIZE // 2)
    float_ball_w.geometry(f"{FT_WINDOW_SIZE}x{FT_WINDOW_SIZE}+{x}+{y}")
    menu = tk.Menu(float_ball_w, tearoff=0)
    menu.configure(borderwidth=0, relief='flat', font=("宋体", 12))
    menu.add_command(label="🌐 翻译屏幕", command=fb_translate_screen)
    menu.add_command(label="💡 解释屏幕", command=fb_explain_screen)
    menu.add_command(label="📝 总结屏幕", command=fb_summary_screen)
    menu.add_separator()
    menu.add_command(label="🎙 切换语音", command=fb_switch_voice)
    menu.add_command(label="📷 切换主动", command=fb_switch_ase)
    menu.add_separator()
    menu.add_command(label="🪟 窗口模式", command=switch_back_window)
    menu.add_separator()
    menu.add_command(label="× 关闭软件", command=on_closing)
    label.bind("<Button-3>", show_menu_fb)  # 右键显示菜单
    float_ball_w.bind("<Button-1>", on_left_button_press)  # 左键按下
    float_ball_w.bind("<B1-Motion>", on_mouse_move)  # 左键拖动
    float_ball_w.mainloop()


FT_WINDOW_SIZE = 50
_start_x, _start_y, _window_x, _window_y = 0, 0, 0, 0
Thread(target=run_chatweb).start()
if voice_break == "开启":
    Thread(target=sense_voice_th_break).start()
else:
    Thread(target=sense_voice_th).start()
Thread(target=run_live2d).start()
Thread(target=run_mmd).start()
Thread(target=run_vrm).start()
Thread(target=refresh_preference).start()
Thread(target=run_ase_rp).start()
Thread(target=run_ase_agent).start()
input_box.bind('<Return>', text_chat)
kb.add_hotkey('alt+g', stop_tts)
try:
    kb.add_hotkey(f'alt+{voice_key}', switch_voice)
except:
    print("语音模式切换按键设置错误")
wydh_icon = Image.open("data/image/ui/wydh.png")
wydh_icon = wydh_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
wydh_icon = ImageTk.PhotoImage(wydh_icon)
Button(root, image=wydh_icon, command=open_chatweb, borderwidth=0, highlightthickness=0).place(relx=0.18, rely=0.02)
vrmjs_icon = Image.open("data/image/ui/vrmjs.png")
vrmjs_icon = vrmjs_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
vrmjs_icon = ImageTk.PhotoImage(vrmjs_icon)
Button(root, image=vrmjs_icon, command=lambda: wb.open(f"http://127.0.0.1:{vrm_port}"), borderwidth=0,
       highlightthickness=0).place(relx=0.27, rely=0.02)
mmdjs_icon = Image.open("data/image/ui/mmdjs.png")
mmdjs_icon = mmdjs_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
mmdjs_icon = ImageTk.PhotoImage(mmdjs_icon)
Button(root, image=mmdjs_icon, command=lambda: wb.open(f"http://127.0.0.1:{mmd_port}"), borderwidth=0,
       highlightthickness=0).place(relx=0.36, rely=0.02)
mmddz_icon = Image.open("data/image/ui/mmddz.png")
mmddz_icon = mmddz_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
mmddz_icon = ImageTk.PhotoImage(mmddz_icon)
Button(root, image=mmddz_icon, command=open_vmd_music, borderwidth=0, highlightthickness=0).place(relx=0.45, rely=0.02)
live2djs_icon = Image.open("data/image/ui/live2djs.png")
live2djs_icon = live2djs_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
live2djs_icon = ImageTk.PhotoImage(live2djs_icon)
Button(root, image=live2djs_icon, command=lambda: wb.open(f"http://127.0.0.1:{live2d_port}"), borderwidth=0,
       highlightthickness=0).place(relx=0.54, rely=0.02)
l2dzc_icon = Image.open("data/image/ui/l2dzc.png")
l2dzc_icon = l2dzc_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
l2dzc_icon = ImageTk.PhotoImage(l2dzc_icon)
Button(root, image=l2dzc_icon, command=open_pet, borderwidth=0, highlightthickness=0).place(relx=0.63, rely=0.02)
zygl_icon = Image.open("data/image/ui/zygl.png")
zygl_icon = zygl_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
zygl_icon = ImageTk.PhotoImage(zygl_icon)
Button(root, image=zygl_icon, command=open_change_w, borderwidth=0, highlightthickness=0).place(relx=0.72, rely=0.02)
rjsz_icon = Image.open("data/image/ui/rjsz.png")
rjsz_icon = rjsz_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
rjsz_icon = ImageTk.PhotoImage(rjsz_icon)
Button(root, image=rjsz_icon, command=open_setting_w, borderwidth=0, highlightthickness=0).place(relx=0.81, rely=0.02)
tzbf_icon = Image.open("data/image/ui/tzbf.png")
tzbf_icon = tzbf_icon.resize((int(100 * scaling_factor), int(23 * scaling_factor)), Image.Resampling.LANCZOS)
tzbf_icon = ImageTk.PhotoImage(tzbf_icon)
Button(root, image=tzbf_icon, command=stop_tts, borderwidth=0, highlightthickness=0).place(relx=0.9, rely=0.02)
upphoto_icon = Image.open("data/image/ui/upphoto.png")
upphoto_icon = upphoto_icon.resize((int(25 * scaling_factor), int(25 * scaling_factor)), Image.Resampling.LANCZOS)
upphoto_icon = ImageTk.PhotoImage(upphoto_icon)
Button(root, image=upphoto_icon, command=up_photo, borderwidth=0, highlightthickness=0).place(relx=0.97, rely=0.825)
export_icon = Image.open("data/image/ui/export.png")
export_icon = export_icon.resize((int(25 * scaling_factor), int(25 * scaling_factor)), Image.Resampling.LANCZOS)
export_icon = ImageTk.PhotoImage(export_icon)
Button(root, image=export_icon, command=export_chat, borderwidth=0, highlightthickness=0).place(relx=0.97, rely=0.865)
add_icon = Image.open("data/image/ui/add.png")
add_icon = add_icon.resize((int(25 * scaling_factor), int(25 * scaling_factor)), Image.Resampling.LANCZOS)
add_icon = ImageTk.PhotoImage(add_icon)
Button(root, image=add_icon, command=clear_chat, borderwidth=0, highlightthickness=0).place(relx=0.97, rely=0.905)
send_icon = Image.open("data/image/ui/send.png")
send_icon = send_icon.resize((int(25 * scaling_factor), int(25 * scaling_factor)), Image.Resampling.LANCZOS)
send_icon = ImageTk.PhotoImage(send_icon)
Button(root, image=send_icon, command=text_chat, borderwidth=0, highlightthickness=0).place(relx=0.97, rely=0.945)
Button(root, text="🔮切换至悬浮球", command=switch_float_ball, borderwidth=0, highlightthickness=0).place(relx=0.02,
                                                                                                         rely=0.11)
Button(root, text="📱手机网页访问", command=open_web_tips, borderwidth=0, highlightthickness=0).place(relx=0.02,
                                                                                                     rely=0.16)
root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
os.kill(os.getpid(), 15)
