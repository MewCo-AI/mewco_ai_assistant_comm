import uuid
from agi_pc_pro import *


def common_chat(msg):
    if mode_menu.get() == "提示词对话":
        output_box.insert("end", f"\n{username}:\n    {msg}\n")
        output_box.see("end")
        notice(f"{asst_name}正在思考中，请稍等...")
        return normal_chat(msg)
    elif mode_menu.get() == "多智能体助手":
        output_box.insert("end", f"\n{username}:\n    {msg}\n")
        output_box.see("end")
        notice(f"{asst_name}正在思考中，请稍等...")
        user_task = user_intent_recognition(msg)
        notice(f"{asst_name}调用了[{user_task}]智能体")
        task_handlers = {
            "音乐播放": (play_music, (msg,)), "语音输入": (voice_input, (msg,)),
            "打开软件/网页": (open_app_select, (msg,)), "音量减小": (vol_down, ()), "音量增大": (vol_up, ()),
            "文本写作": (auto_input, (msg,)), "表格制作": (make_excel, (msg,)),
            "翻译屏幕内容": (translate_screen, (msg,)), "解释屏幕内容": (explain_screen, (msg,)),
            "总结屏幕内容": (summary_screen, (msg,)), "续写屏幕内容": (continue_write_screen, (msg,)),
            "灯类智能家居控制": (control_ha_lamp, ()), "风扇类智能家居控制": (control_ha_fan, ()),
            "插座类智能家居控制": (control_ha_plug, ()), "天气查询": (get_weather, (msg,)),
            "热搜新闻": (get_news, (msg,)), "PPT制作": (make_ppt, (msg,)),
            "系统状态查询": (get_system_state, (msg,)), "联网搜索": (ol_search, (msg,)),
            "视频生成": (generate_video, (msg,)), "网页开发": (develop_web, (msg,))}
        for task, (handler, args) in task_handlers.items():
            if task in user_task:
                return handler(*args)
        else:
            return normal_chat(msg)
    elif mode_menu.get() == "自主操控Lite":
        run_agi_pc_lite(msg)
        return "OK"
    elif mode_menu.get() == "自主操控Pro":
        if agi_pc_pro_api_key == "":
            messagebox.showinfo("提示", "请先前往软件设置→自主操控Pro→配置密钥api_key\n保存后重启软件生效")
            return "请先前往软件设置→自主操控Pro→配置密钥api_key，保存后重启软件生效"
        else:
            run_agi_pc_pro(msg)
            return "OK"
    elif mode_menu.get() == "OpenClaw龙虾":
        if openclaw_api_key == "":
            messagebox.showinfo("提示", "请先前往软件设置→OpenClaw龙虾→配置密钥api_key\n保存后重启软件生效")
            return "请先前往软件设置→OpenClaw龙虾→配置密钥api_key，保存后重启软件生效"
        else:
            output_box.insert("end", f"\n{username}:\n    {msg}\n")
            output_box.see("end")
            notice(f"{asst_name}正在调用OpenClaw龙虾，请稍等...")
            res = chat_openclaw(msg)
            res = res.replace("#", "").replace("*", "")
            stream_insert(f"{asst_name}:\n    {res}\n")
            get_tts_play(res)
            return res
    else:
        if mqtt_switch != "开启":
            messagebox.showinfo("提示", "请先前往软件设置→MQTT/QwenPaw→开启MQTT开关\n保存后重启软件生效")
            return "请先前往软件设置→MQTT/QwenPaw→开启MQTT开关，保存后重启软件生效"
        else:
            output_box.insert("end", f"\n{username}:\n    {msg}\n")
            output_box.see("end")
            notice(f"{asst_name}正在通过MQTT调用QwenPaw助理，请稍等...")
            try:
                return run_mqtt_qwenpaw(mq_client, msg)
            except:
                notice(f"MQTT未正确配置")
                stream_insert(f"{asst_name}:\n    MQTT未正确配置\n")
                get_tts_play("MQTT未正确配置")
                return "MQTT未正确配置"


def chat_openclaw(msg):
    try:
        client = OpenAI(api_key=openclaw_api_key, base_url=f"{openclaw_gateway}/v1")
        messages = [{"role": "system", "content": openclaw_prompt}, {"role": "user", "content": msg}]
        completion = client.chat.completions.create(model=openclaw_model, messages=messages, stream=False)
        notice("收到OpenClaw龙虾回复")
        return completion.choices[0].message.content.strip()
    except Exception as e2:
        notice(f"OpenClaw龙虾调用异常，错误详情：{e2}")
        return "OpenClaw龙虾调用异常"


def normal_chat(msg):
    bot_response = chat_preprocess(msg)
    bot_response = bot_response.replace("#", "").replace("*", "")
    stream_insert(f"{asst_name}:\n    {bot_response}\n")
    get_tts_play(bot_response)
    return bot_response


def open_app_select(msg):
    def find_app_path(app_path):
        possible_paths = [
            f"C:/Program Files (x86)/{app_path}", f"C:/Program Files/{app_path}", f"D:/Program Files (x86)/{app_path}",
            f"D:/Program Files/{app_path}", f"E:/Program Files (x86)/{app_path}", f"E:/Program Files/{app_path}",
            f"F:/Program Files (x86)/{app_path}", f"F:/Program Files/{app_path}",
            os.path.join(os.environ['APPDATA'], app_path)]
        for path2 in possible_paths:
            if os.path.exists(path2):
                return path2
        return None

    def open_app(app_name2, app_path):
        app_full_path = find_app_path(app_path)
        if app_full_path:
            Popen(app_full_path)
            notice(f"{asst_name}打开了{app_name2}")
            get_tts_play(f"好的，已为您打开{app_name2}")
        else:
            stream_insert(f"{asst_name}:\n    未找到{app_name2}安装路径\n")
            notice(f"未找到{app_name2}安装路径")
            get_tts_play(f"未找到{app_name2}安装路径")

    app_mappings = {
        '微信': ('微信', 'Tencent/Weixin/Weixin.exe'), 'QQ': ('QQ', 'Tencent/QQNT/QQ.exe'),
        '文档': ('Word文档', 'Microsoft Office/root/Office16/WINWORD.EXE'),
        '音乐': ('网易云音乐', 'NetEase/CloudMusic/cloudmusic.exe'),
        '崩坏': ('崩坏：星穹铁道', 'miHoYo Launcher/games/Star Rail Game/StarRail.exe'),
        '原神': ('原神', 'miHoYo Launcher/games/Genshin Impact Game/YuanShen.exe'),
        '元神': ('原神', 'miHoYo Launcher/games/Genshin Impact Game/YuanShen.exe'),
        '绝区零': ('绝区零', 'miHoYo Launcher/games/ZenlessZoneZero Game/ZenlessZoneZero.exe'),
        '区灵': ('绝区零', 'miHoYo Launcher/games/ZenlessZoneZero Game/ZenlessZoneZero.exe'),
        '白禁区': ('尘白禁区', 'SeasunCBJQos/SeasunGame.exe'),
        '明日方舟': ('明日方舟：终末地', 'Hypergryph Launcher/games/Endfield Game/Endfield.exe'),
        '终末': ('明日方舟：终末地', 'Hypergryph Launcher/games/Endfield Game/Endfield.exe'),
        '魔兽': ('魔兽世界', 'World of Warcraft/_retail_/wow.exe'),
        '二重': ('二重螺旋', 'Duet Night Abyss/DNA Game/EM.exe'),
        '螺旋': ('二重螺旋', 'Duet Night Abyss/DNA Game/EM.exe'),
        '鸣潮': ('鸣潮', 'Wuthering Waves/Wuthering Waves Game/Wuthering Waves.exe'), '记事本': ('记事本', None),
        '便签': ('记事本', None), '备忘录': ('记事本', None), '笔记': ('记事本', None), '计算器': ('计算器', None),
        '文件管理': ('资源管理器', None), '资源管理': ('资源管理器', None), '任务管理': ('任务管理器', None),
        '画图': ('画图工具', None), '绘图': ('画图工具', None), '控制面板': ('控制面板', None)}
    special_commands = {'悟空': ('黑神话：悟空', 'steam://rungameid/2358720', wb.open),
                        '神话': ('黑神话：悟空', 'steam://rungameid/2358720', wb.open),
                        '饥荒': ('饥荒', 'steam://rungameid/322330', wb.open),
                        '泰拉瑞亚': ('泰拉瑞亚', 'steam://rungameid/105600', wb.open),
                        '地平线5': ('地平线5', 'steam://rungameid/1551360', wb.open),
                        '地平线': ('地平线4', 'steam://rungameid/1293830', wb.open),
                        '逃离': ('逃离鸭科夫', 'steam://rungameid/3167020', wb.open),
                        '我的世界': ('我的世界', 'fevergames://mygame/?gameId=1', wb.open),
                        'MC': ('我的世界', 'fevergames://mygame/?gaImed=1', wb.open)}
    builtin_commands = {
        '记事本': ('notepad', Popen), '计算器': ('calc', Popen), '资源管理器': ('explorer', Popen),
        '任务管理器': ('taskmgr', Popen), '画图工具': ('mspaint', Popen), '控制面板': ('control', Popen)}
    for keyword, (app_name, path, func) in special_commands.items():
        if keyword in msg:
            func(path)
            notice(f"{asst_name}打开了{app_name}")
            get_tts_play(f"好的，已为您打开{app_name}")
            return f"好的，已为您打开{app_name}"
    for keyword, (app_name, path) in app_mappings.items():
        if keyword in msg:
            if path is None:
                cmd, func = builtin_commands[app_name]
                func(cmd)
                notice(f"{asst_name}打开了{app_name}")
                get_tts_play(f"好的，已为您打开{app_name}")
            else:
                open_app(app_name, path)
            return f"好的，已为您打开{app_name}"
    try:
        content = function_llm(
            "请你扮演一个Windows CMD命令转换器。每当我输入自然语言命令时，你必须仅输出对应的CMD命令，不能添加任何其他文字或说明。",
            msg)
        result = os.system(content)
        if result == 0:
            notice(f"{asst_name}接管了电脑")
        else:
            text_to_cmd_error = "抱歉，这个我还不会，可尝试更换对话语言模型"
            stream_insert(f"{asst_name}:\n    {text_to_cmd_error}\n")
            notice(text_to_cmd_error)
            get_tts_play(text_to_cmd_error)
            return text_to_cmd_error
    except:
        text_to_cmd_error = "暂不支持打开该软件"
        stream_insert(f"{asst_name}:\n    {text_to_cmd_error}\n")
        notice(text_to_cmd_error)
        get_tts_play(text_to_cmd_error)
        return text_to_cmd_error


def run_mqtt_qwenpaw(client, text):
    msg_data = {"text": text, "redirect_client_id": mq_client_id}
    msg = json.dumps(msg_data, ensure_ascii=False)
    result = client.publish(mq_pub_topic, msg, qos=mq_qos)
    result.wait_for_publish()
    if result.is_published():
        return "发送成功"
    else:
        return "发送失败"


def connect_mqtt():
    def on_connect(client1, userdata, flags, rc):
        if rc == 0:
            print("连接MQTT服务器成功！")
            client1.subscribe(mq_sub_topic, qos=mq_qos)  # 订阅机器人回复主题
        else:
            print(f"连接MQTT服务器失败，错误码：{rc}")

    client = mqtt_client.Client(client_id=mq_client_id, transport="tcp")
    client.on_connect = on_connect
    client.on_message = mqtt_on_message  # 绑定消息接收回调
    client.connect(mq_host, mq_port)
    return client


def mqtt_on_message(client, userdata, msg):
    try:
        res = msg.payload.decode("utf-8").strip()
        res = res.replace("#", "").replace("*", "")
        notice("收到MQTT/QwenPaw回复")
        stream_insert(f"{asst_name}:\n    {res}\n")
        get_tts_play(res)
    except Exception as e2:
        notice(f"MQTT/QwenPaw回复异常：{e2}")
        stream_insert(f"{asst_name}:\n    QwenPaw回复异常\n")
        get_tts_play("QwenPaw回复异常")


if mqtt_switch == "开启":
    from paho.mqtt import client as mqtt_client

    mq_client_id = uuid.uuid1().hex[-6:]
    try:
        mq_client = connect_mqtt()
        mq_client.loop_start()
    except Exception as e:
        print(f"连接MQTT服务器失败：{e}")
