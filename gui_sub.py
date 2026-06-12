import os
import tkinter as tk
import webbrowser as wb
from tkinter import ttk, Label, Text, StringVar, Menu, Button, Entry
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
from gui_qt import *

draw_img = None
scaling_factor = 1


def notice(info):
    state_box.delete("1.0", "end")
    state_box.insert("end", info)


def msg_box(title, msg):
    global msg_w
    msg_w = tk.Toplevel(root)
    msg_w.geometry("640x480")
    msg_w.attributes("-topmost", 1)
    msg_w.title(title)
    msg_text = ScrolledText(msg_w)
    msg_text.insert("end", msg)
    msg_text.configure(state="disabled")
    msg_text.pack()
    msg_w.iconbitmap("data/image/logo.ico")
    msg_w.bind("<Button-3>", show_menu_msg)


def draw_box(w_name, draw_name):
    global draw_w, draw_img
    try:
        draw_w.destroy()
    except:
        pass
    draw_w = tk.Toplevel(root)
    draw_w.geometry("900x900")
    draw_w.resizable(False, False)
    draw_w.attributes("-topmost", 1)
    draw_w.title(f"{w_name} AI生成图像 - 枫云AI助手社区版")
    draw_img = Image.open(f"data/cache/draw/{draw_name}.png")
    draw_img = draw_img.resize((900, 900), Image.Resampling.LANCZOS)
    draw_img = ImageTk.PhotoImage(draw_img)
    Label(draw_w, image=draw_img).pack()
    Label(draw_w, text="AI生成", font=("黑体", 20)).place(relx=0.01, rely=0.95)
    draw_w.iconbitmap("data/image/logo.ico")


def show_menu_msg(event):
    menu = Menu(msg_w, tearoff=0)
    menu.add_command(label="📄复制 Ctrl+C", command=lambda: msg_w.focus_get().event_generate('<<Copy>>'))
    menu.post(event.x_root, event.y_root)


def show_menu(event):
    menu = Menu(root, tearoff=0)
    menu.add_command(label="✂剪切 Ctrl+X", command=lambda: root.focus_get().event_generate('<<Cut>>'))
    menu.add_command(label="📄复制 Ctrl+C", command=lambda: root.focus_get().event_generate('<<Copy>>'))
    menu.add_command(label="📋粘贴 Ctrl+V", command=lambda: root.focus_get().event_generate('<<Paste>>'))
    menu.add_separator()
    menu.add_command(label="🗑删除 Del", command=lambda: root.focus_get().event_generate('<<Clear>>'))
    menu.add_separator()
    menu.add_command(label="清空聊天记录(保留记忆)", command=del_history)
    menu.add_command(label="删除记忆(保留聊天记录)", command=del_memory)
    menu.add_separator()
    menu.add_command(label="备份与恢复 - 导出记忆", command=export_memory)
    menu.add_command(label="备份与恢复 - 导入记忆", command=import_memory)
    menu.post(event.x_root, event.y_root)


def del_history():
    if messagebox.askokcancel(f"清空聊天记录(保留记忆)", del_history_alarm):
        output_box.delete("1.0", "end")
        notice("聊天记录已清空")


def del_memory():
    if messagebox.askokcancel(f"删除记忆(保留聊天记录)", del_memory_alarm):
        with open('data/db/memory.db', 'w', encoding='utf-8') as f:
            f.write("")
        notice("记忆已删除，请立即重启软件生效")


def export_memory():
    try:
        source_file = 'data/db/memory.db'
        default_filename = "memory_backup.db"
        save_path = (fd.asksaveasfilename(defaultextension=".db", filetypes=[("数据库文件", "*.db")],
                                          initialfile=default_filename, title="选择记忆备份保存位置"))
        if save_path:
            shutil.copy2(source_file, save_path)
            messagebox.showinfo("导出成功", f"记忆已备份到：{save_path}")
    except Exception as e:
        messagebox.showerror("导出失败", f"导出记忆时发生错误，详情：{e}")


def import_memory():
    try:
        target_dir = 'data/db'
        file_path = fd.askopenfilename(filetypes=[("数据库文件", "*.db")], title="选择要导入的记忆备份文件")
        if not file_path:
            return
        if messagebox.askyesno("确认导入", f"您确定要导入此记忆文件吗？\n导入后需重启软件生效"):
            target_file = os.path.join(target_dir, 'memory.db')
            shutil.copy2(file_path, target_file)
            messagebox.showinfo("导入成功", "记忆导入成功！请立即重启软件生效")
    except Exception as e:
        messagebox.showerror("导入失败", f"导入记忆时发生错误，详情：{e}")


def scaled_size(original_size):
    global scaling_factor
    dpi = get_dpi()
    scaling_factor = dpi / 96
    return int(original_size[0] * scaling_factor), int(original_size[1] * scaling_factor)


def open_live2d_set_w():
    def read_settings():
        settings = {}
        with open('dist/assets/live2d_core/live2d_js_set.txt', 'r', encoding='utf-8') as f:
            lines1 = f.readlines()
            current_key = None
            for line in lines1:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_key = line[1:-1].strip()
                elif current_key:
                    settings[current_key] = line
                    current_key = None
        return settings

    def save_settings(settings):
        entry_model_path2 = live2d_menu.get().replace('\\', '/')
        with open('dist/assets/live2d_core/live2d_js_set.txt', 'w', encoding='utf-8') as f:
            for key, value in settings.items():
                f.write(f'[{key}]\n{value}\n\n')
        with open('dist/assets/live2d.js', 'w', encoding='utf-8') as f:
            f.write(
                live2d_js_part1 + entry_model_path2 + live2d_js_part2 + entry_model_x.get() + live2d_js_part3 + entry_model_y.get() + live2d_js_part4 + entry_model_size.get() + live2d_js_part5)

    def on_save():
        entry_model_path2 = live2d_menu.get().replace('\\', '/')
        settings = {"模型路径": entry_model_path2, "模型横坐标": entry_model_x.get(),
                    "模型纵坐标": entry_model_y.get(), "模型大小": entry_model_size.get()}
        save_settings(settings)
        messagebox.showinfo("保存成功", "Live2D设置已保存！\n右键重新加载桌宠生效")

    def find_model3_json_files():
        live2d_folder = 'dist/assets/live2d_model'
        model3_files = []
        for root2, dirs, files in os.walk(live2d_folder):
            for f in files:
                if f.endswith('.model3.json'):
                    relative_path = os.path.relpath(os.path.join(root2, f), live2d_folder)
                    model3_files.append(relative_path)
        return model3_files

    def load_settings():
        settings = read_settings()
        live2d_var.set(settings.get("模型路径", ""))
        entry_model_x.insert(0, settings.get("模型横坐标", ""))
        entry_model_y.insert(0, settings.get("模型纵坐标", ""))
        entry_model_size.insert(0, settings.get("模型大小", ""))

    live2d_set_w = tk.Toplevel(root)
    live2d_set_w.title("Live2D设置 - 枫云AI助手社区版")
    original_window_size4 = (413, 310)
    scaled_window_size4 = scaled_size(original_window_size4)
    live2d_set_w.geometry(f"{scaled_window_size4[0]}x{scaled_window_size4[1]}")
    Label(live2d_set_w, text="Live2D设置", font=("楷体", 18, "bold"), fg="#587EF4").pack(pady=10)
    Label(live2d_set_w, text="模型路径:").pack()
    model3_options = find_model3_json_files()
    live2d_var = StringVar(root)
    live2d_menu = ttk.Combobox(live2d_set_w, textvariable=live2d_var, values=model3_options, state="readonly",
                               justify='center', width=43, font=("楷体", 13))
    live2d_menu.pack()
    Label(live2d_set_w, text="模型横坐标:").pack()
    entry_model_x = Entry(live2d_set_w, width=5)
    entry_model_x.pack()
    Label(live2d_set_w, text="模型纵坐标:").pack()
    entry_model_y = Entry(live2d_set_w, width=5)
    entry_model_y.pack()
    Label(live2d_set_w, text="模型大小:").pack()
    entry_model_size = Entry(live2d_set_w, width=2)
    entry_model_size.pack()
    button_frame = tk.Frame(live2d_set_w)
    button_frame.pack(pady=10)
    Button(button_frame, text="取消", command=live2d_set_w.destroy).pack(side='left', padx=5)
    Button(button_frame, text="保存", command=on_save, bg="#2A6EE9", fg="white").pack(side='left', padx=5)
    load_settings()
    live2d_set_w.iconbitmap("data/image/logo.ico")
    live2d_set_w.mainloop()


def open_mmd_set_w():
    def read_settings():
        settings = {}
        with open('dist/assets/mmd_core/mmd_js_set.txt', 'r', encoding='utf-8') as f:
            lines1 = f.readlines()
            current_key = None
            for line in lines1:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_key = line[1:-1].strip()
                elif current_key:
                    settings[current_key] = line
                    current_key = None
        return settings

    def save_settings(settings):
        entry_model_path2 = mmd_menu.get().replace('\\', '/')
        with open('dist/assets/mmd_core/mmd_js_set.txt', 'w', encoding='utf-8') as f:
            for key, value in settings.items():
                f.write(f'[{key}]\n{value}\n\n')
        with open('dist/assets/mmd.js', 'w', encoding='utf-8') as f:
            f.write(
                mmd_js_part1 + entry_model_path2 + mmd_js_part2 + entry_mouth_index.get() + mmd_js_part3 + entry_eye_index.get() + mmd_js_part4)
        with open('dist/assets/mmd_vmd.js', 'w', encoding='utf-8') as f:
            f.write(mmd_vmd_js_part1 + entry_model_path2 + mmd_vmd_js_part2 + vmd_menu.get() + mmd_vmd_js_part3)

    def on_save():
        entry_model_path2 = mmd_menu.get().replace('\\', '/')
        settings = {"模型路径": entry_model_path2, "动作路径": vmd_menu.get(),
                    "模型嘴索引": entry_mouth_index.get(), "模型眼索引": entry_eye_index.get()}
        save_settings(settings)
        messagebox.showinfo("保存成功", "MMD 3D设置已保存！\n刷新MMD 3D角色网页生效")

    def find_pmx_files():
        mmd_folder = 'dist/assets/mmd_model'
        pmx_files = []
        for root2, dirs, files in os.walk(mmd_folder):
            for f in files:
                if f.endswith('.pmx'):
                    relative_path = os.path.relpath(os.path.join(root2, f), mmd_folder)
                    pmx_files.append(relative_path)
        return pmx_files

    def find_vmd_files():
        vmd_folder = 'dist/assets/mmd_action'
        vmd_files = []
        for root2, dirs, files in os.walk(vmd_folder):
            for f in files:
                if f.endswith('.vmd'):
                    relative_path = os.path.relpath(os.path.join(root2, f), vmd_folder)
                    vmd_files.append(relative_path)
        return vmd_files

    def load_settings():
        settings = read_settings()
        mmd_var.set(settings.get("模型路径", ""))
        vmd_var.set(settings.get("动作路径", ""))
        entry_mouth_index.insert(0, settings.get("模型嘴索引", ""))
        entry_eye_index.insert(0, settings.get("模型眼索引", ""))

    mmd_set_w = tk.Toplevel(root)
    mmd_set_w.title("MMD 3D设置 - 枫云AI助手社区版")
    original_window_size4 = (413, 310)
    scaled_window_size4 = scaled_size(original_window_size4)
    mmd_set_w.geometry(f"{scaled_window_size4[0]}x{scaled_window_size4[1]}")
    Label(mmd_set_w, text="MMD 3D设置", font=("楷体", 18, "bold"), fg="#587EF4").pack(pady=10)
    Label(mmd_set_w, text="模型路径:").pack()
    pmx_options = find_pmx_files()
    mmd_var = StringVar(root)
    mmd_menu = ttk.Combobox(mmd_set_w, textvariable=mmd_var, values=pmx_options, state="readonly",
                            justify='center', width=43, font=("楷体", 13))
    mmd_menu.pack()
    Label(mmd_set_w, text="动作路径:").pack()
    vmd_options = find_vmd_files()
    vmd_var = StringVar(root)
    vmd_menu = ttk.Combobox(mmd_set_w, textvariable=vmd_var, values=vmd_options, state="readonly",
                            justify='center', width=43, font=("楷体", 13))
    vmd_menu.pack()
    Label(mmd_set_w, text="模型嘴索引:").pack()
    entry_mouth_index = Entry(mmd_set_w, width=4)
    entry_mouth_index.pack()
    Label(mmd_set_w, text="模型眼索引:").pack()
    entry_eye_index = Entry(mmd_set_w, width=4)
    entry_eye_index.pack()
    button_frame = tk.Frame(mmd_set_w)
    button_frame.pack(pady=10)
    Button(button_frame, text="取消", command=mmd_set_w.destroy).pack(side='left', padx=5)
    Button(button_frame, text="保存", command=on_save, bg="#2A6EE9", fg="white").pack(side='left', padx=5)
    load_settings()
    mmd_set_w.iconbitmap("data/image/logo.ico")
    mmd_set_w.mainloop()


def open_vrm_set_w():
    def on_save():
        with open('data/db/vrm_model_name.db', 'w', encoding="utf-8") as f:
            f.write(vrm_menu.get())
        messagebox.showinfo("保存成功", "VRM 3D设置已保存！\n重启软件生效")

    def find_vrm_files():
        vrm_folder = 'dist/assets/vrm_model'
        vrm_files = []
        for root2, dirs, files in os.walk(vrm_folder):
            for f in files:
                if f.endswith('.vrm'):
                    relative_path = os.path.relpath(os.path.join(root2, f), vrm_folder)
                    vrm_files.append(relative_path)
        return vrm_files

    vrm_set_w = tk.Toplevel(root)
    vrm_set_w.title("VRM 3D设置 - 枫云AI助手社区版")
    original_window_size4 = (413, 160)
    scaled_window_size4 = scaled_size(original_window_size4)
    vrm_set_w.geometry(f"{scaled_window_size4[0]}x{scaled_window_size4[1]}")
    Label(vrm_set_w, text="VRM 3D设置", font=("楷体", 18, "bold"), fg="#587EF4").pack(pady=10)
    Label(vrm_set_w, text="模型名称:").pack()
    vrm_options = find_vrm_files()
    vrm_var = StringVar(root)
    vrm_var.set(vrm_model_name)
    vrm_menu = ttk.Combobox(vrm_set_w, textvariable=vrm_var, values=vrm_options, state="readonly",
                            justify='center', width=43, font=("楷体", 13))
    vrm_menu.pack()
    button_frame = tk.Frame(vrm_set_w)
    button_frame.pack(pady=10)
    Button(button_frame, text="取消", command=vrm_set_w.destroy).pack(side='left', padx=5)
    Button(button_frame, text="保存", command=on_save, bg="#2A6EE9", fg="white").pack(side='left', padx=5)
    vrm_set_w.iconbitmap("data/image/logo.ico")
    vrm_set_w.mainloop()


def open_change_w():
    def open_music_folder():
        os.startfile("data\\music")
        os.startfile("data\\music_vmd")

    change_w = tk.Toplevel(root)
    change_w.title("资源管理 - 枫云AI助手社区版")
    original_window_size3 = (1000, 375)
    scaled_window_size3 = scaled_size(original_window_size3)
    change_w.geometry(f"{scaled_window_size3[0]}x{scaled_window_size3[1]}")
    Label(change_w, text="更换Live2D模型", font=("楷体", 18, "bold"), fg="#587EF4").place(relx=0.03, rely=0.0367)
    Label(change_w, text='第1步:\n推荐从模之屋下载模型\n格式选择Live2D', font=("楷体", 12)).place(relx=0.01,
                                                                                                  rely=0.1667)
    Button(change_w, text="下载", command=lambda: wb.open(mzw_model_url), bg="#3E92ED", fg="white").place(relx=0.18,
                                                                                                          rely=0.2)
    Label(change_w, text='第2步:\n打开模型文件夹,\n放入下载解压好的模型', font=("楷体", 12)).place(relx=0.01, rely=0.45)
    Button(change_w, text="打开", command=lambda: os.startfile("dist\\assets\\live2d_model"), bg="#3E92ED",
           fg="white").place(relx=0.18, rely=0.5)
    Label(change_w, text='第3步:\n点击配置按钮\n进行路径和参数设置', font=("楷体", 12)).place(relx=0.02, rely=0.75)
    Button(change_w, text="配置", command=open_live2d_set_w, bg="#3E92ED", fg="white").place(relx=0.18, rely=0.8)
    Label(change_w, text="更换MMD 3D模型", font=("楷体", 18, "bold"), fg="#587EF4").place(relx=0.26, rely=0.0367)
    Label(change_w, text='第1步:\n推荐从模之屋下载模型,动作\n模型格式选MMD,类型选人物\n动作类型选人物动作',
          font=("楷体", 12)).place(relx=0.25, rely=0.15)
    Button(change_w, text="模型", command=lambda: wb.open(mzw_model_url), bg="#3E92ED", fg="white").place(relx=0.46,
                                                                                                          rely=0.15)
    Button(change_w, text="动作", command=lambda: wb.open("https://www.aplaybox.com/model/action"), bg="#3E92ED",
           fg="white").place(relx=0.46,
                             rely=0.25)
    Label(change_w, text='第2步:\n打开模型文件夹,\n放入下载解压好的模型', font=("楷体", 12)).place(relx=0.27, rely=0.37)
    Button(change_w, text="打开", command=lambda: os.startfile("dist\\assets\\mmd_model"), bg="#3E92ED",
           fg="white").place(relx=0.46, rely=0.42)
    Label(change_w, text='第3步:\n打开动作文件夹,\n放入下载解压好的动作', font=("楷体", 12)).place(relx=0.27, rely=0.57)
    Button(change_w, text="打开", command=lambda: os.startfile("dist\\assets\\mmd_action"), bg="#3E92ED",
           fg="white").place(relx=0.46, rely=0.62)
    Label(change_w, text='第4步:\n点击配置按钮\n进行路径和参数设置', font=("楷体", 12)).place(relx=0.28, rely=0.77)
    Button(change_w, text="配置", command=open_mmd_set_w, bg="#3E92ED", fg="white").place(relx=0.46, rely=0.82)
    Label(change_w, text="更换VRM 3D模型", font=("楷体", 18, "bold"), fg="#587EF4").place(relx=0.55, rely=0.0367)
    Label(change_w, text='第1步:\n使用VRoid建模导出VRM\n或从模之屋下载模型\n格式选择VRM', font=("楷体", 12)).place(
        relx=0.54, rely=0.15)
    Button(change_w, text="下载", command=lambda: wb.open(mzw_model_url), bg="#3E92ED", fg="white").place(relx=0.71,
                                                                                                          rely=0.2)
    Label(change_w, text='第2步:\n打开模型文件夹,\n放入下载解压好的模型', font=("楷体", 12)).place(relx=0.54, rely=0.45)
    Button(change_w, text="打开", command=lambda: os.startfile("dist\\assets\\vrm_model"), bg="#3E92ED",
           fg="white").place(relx=0.71, rely=0.5)
    Label(change_w, text='第3步:\n点击配置按钮\n进行路径和参数设置', font=("楷体", 12)).place(relx=0.55, rely=0.75)
    Button(change_w, text="配置", command=open_vrm_set_w, bg="#3E92ED", fg="white").place(relx=0.71, rely=0.8)
    Label(change_w, text="更换Web背景", font=("楷体", 18, "bold"), fg="#587EF4").place(relx=0.78, rely=0.0367)
    Label(change_w, text='第1步:\n上传一张图片,\n格式需要为jpg', font=("楷体", 12)).place(relx=0.79, rely=0.15)
    Button(change_w, text="上传图片", command=upload_image, bg="#3E92ED", fg="white").place(relx=0.8, rely=0.31)
    Label(change_w, text='第2步:\n刷新网页', font=("楷体", 12)).place(relx=0.81, rely=0.42)
    Label(change_w, text="头像管理", font=("楷体", 18, "bold"), fg="#587EF4").place(relx=0.80, rely=0.54)
    Label(change_w, text='头像文件夹\n(格式需要为png)', font=("楷体", 12)).place(relx=0.79, rely=0.62)
    Button(change_w, text="打开", command=lambda: os.startfile("data\\image\\ch"), bg="#3E92ED", fg="white").place(
        relx=0.93, rely=0.62)
    Label(change_w, text="音乐管理", font=("楷体", 18, "bold"), fg="#587EF4").place(relx=0.80, rely=0.75)
    Label(change_w, text='音乐文件夹\n(格式需要为mp3)', font=("楷体", 12)).place(relx=0.79, rely=0.83)
    Button(change_w, text="打开", command=open_music_folder, bg="#3E92ED", fg="white").place(relx=0.93, rely=0.83)
    change_w.iconbitmap("data/image/logo.ico")


original_window_size = (1280, 720)
scaled_window_size = scaled_size(original_window_size)
root = tk.Tk()
root.title("枫云AI助手社区版 v4.2")
root.geometry(f"{scaled_window_size[0]}x{scaled_window_size[1]}")
root.attributes('-alpha', 0.95)
root.configure(bg="#F4F4F4")
root.option_add('*Font', '楷体 15')
root.option_add("*Background", "#F4F4F4")
root.option_add("*Foreground", "black")
logo_img = Image.open("data/image/logo.png")
logo_img = logo_img.resize((int(30 * scaling_factor), int(30 * scaling_factor)), Image.Resampling.LANCZOS)
logo_photo = ImageTk.PhotoImage(logo_img)
try:
    head_img = Image.open(f"data/image/ch/{asst_name}.png")
except:
    head_img = Image.open("data/image/logo.png")
head_img = head_img.resize((int(50 * scaling_factor), int(50 * scaling_factor)), Image.Resampling.LANCZOS)
head_photo = ImageTk.PhotoImage(head_img)
head_label = Label(root, image=head_photo)
head_label.place(relx=0.01, rely=0.01)
Label(root, text=f"我的AI助手:\n{asst_name}").place(relx=0.06, rely=0.02)
Label(root, text="🔧运行模式切换").place(relx=0.02, rely=0.22)
mode_var = StringVar(root)
mode_var.set(prefer_mode)
mode_menu = ttk.Combobox(root, textvariable=mode_var, values=mode_options, width=14, state="readonly", justify='center')
mode_menu.place(relx=0.02, rely=0.26)
Label(root, text="🎙语音识别模式").place(relx=0.02, rely=0.33)
voice_var = StringVar(root)
voice_var.set(voice_switch)
asr_menu = ttk.Combobox(root, textvariable=voice_var, values=voice_options, width=14,
                        state="readonly", justify='center')
asr_menu.place(relx=0.02, rely=0.37)
Label(root, text="🤖对话语言模型").place(relx=0.02, rely=0.44)
llm_var = StringVar(root)
llm_var.set(prefer_llm)
llm_menu = ttk.Combobox(root, textvariable=llm_var, values=llm_options, height=16, width=14, state="readonly",
                        justify='center')
llm_menu.place(relx=0.02, rely=0.48)
Label(root, text="🔊语音合成引擎").place(relx=0.02, rely=0.55)
tts_var = StringVar(root)
tts_var.set(prefer_tts)
tts_menu = ttk.Combobox(root, textvariable=tts_var, values=tts_options, height=12, width=14, state="readonly",
                        justify='center')
tts_menu.place(relx=0.02, rely=0.59)
Label(root, text="🖼图像识别引擎").place(relx=0.02, rely=0.66)
img_var = StringVar(root)
img_var.set(prefer_img)
img_menu = ttk.Combobox(root, textvariable=img_var, values=img_options, width=14, state="readonly", justify='center')
img_menu.place(relx=0.02, rely=0.7)
Label(root, text="📷主动感知对话").place(relx=0.02, rely=0.77)
ase_options = ["高活跃", "中活跃", "低活跃", "不主动"]
ase_var = StringVar(root)
ase_var.set(ase_switch)
ase_menu = ttk.Combobox(root, textvariable=ase_var, values=ase_options, width=14, state="readonly", justify='center')
ase_menu.place(relx=0.02, rely=0.81)
output_box = ScrolledText(root, width=85, height=22, font=("楷体", 18))
output_box.place(relx=0.175, rely=0.08)
output_box.insert('end', history)
output_box.see("end")
input_box = ScrolledText(root, width=82, height=4, font=("楷体", 18))
input_box.place(relx=0.175, rely=0.845)
state_box = Text(root, width=18, height=3, fg="blue")
state_box.place(relx=0.015, rely=0.88)
state_box.insert("end", "欢迎使用枫云AI助手")
Label(root, text="内容由AI生成,请仔细甄别", font=("楷体", 10), fg="green").place(relx=0.02, rely=0.97)
root.iconbitmap("data/image/logo.ico")
root.bind("<Button-3>", show_menu)
