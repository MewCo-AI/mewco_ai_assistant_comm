import platform
from rapidocr_openvino import RapidOCR
from agent import *

ocr = None
should_stop = False  # 全局停止标志
cache_img_path = "data/cache/cache.png"


def current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def on_esc_pressed(e):
    global should_stop
    if e.event_type == kb.KEY_DOWN and e.name == 'esc':
        should_stop = True
        print("\n用户按下ESC键，停止执行")


def get_screen_text():  # 获取屏幕上的文本内容
    global ocr
    if ocr is None:
        ocr = RapidOCR()
    screenshot = pag.screenshot()
    screenshot.save(cache_img_path)
    result, _ = ocr(cache_img_path)
    os.remove(cache_img_path)
    if result is None:
        print("识别结果为空")
        return "未找到"
    all_text = []
    for line in result:  # 保存文本位置信息，格式: 文本内容(x1,y1,x2,y2)
        text = f"{line[1]}({int(line[0][0][0])},{int(line[0][0][1])},{int(line[0][2][0])},{int(line[0][2][1])})"
        all_text.append(text)
    return "\n".join(all_text)


def ocr_click_text(input_text):  # 识别屏幕上的文本并点击
    global ocr
    if ocr is None:
        ocr = RapidOCR()
    screenshot = pag.screenshot()
    screenshot.save(cache_img_path)  # 保存截图到文件
    print(f"正在识别截图中包含'{input_text}'的文字...")
    result, _ = ocr(cache_img_path)
    os.remove(cache_img_path)
    search_position = None
    for line in result:
        text = line[1]
        if input_text in text:
            bbox = line[0]
            x_min, y_min = min(bbox, key=lambda x: x[0])[0], min(bbox, key=lambda x: x[1])[1]
            x_max, y_max = max(bbox, key=lambda x: x[0])[0], max(bbox, key=lambda x: x[1])[1]
            center_x = (x_min + x_max) / 2
            center_y = (y_min + y_max) / 2
            search_position = (center_x, center_y)
            break
    if search_position is None:
        print(f"未找到包含'{input_text}'的文字")
        return False
    else:
        print(f"找到包含'{input_text}'的文字，坐标为:{search_position}，点击完成")
        scr_txt = str(get_screen_text())
        pag.click(search_position)
        if "此电脑" in scr_txt or "回收站" in scr_txt or "Edge" in scr_txt or "Chrome" in scr_txt:
            time.sleep(0.1)
            pag.click(search_position)
        return True


def analyze_command(command):  # 分析命令并生成执行步骤
    screen_text = get_screen_text()  # 获取屏幕文本和尺寸信息，帮助AI做决策
    agi_pc_lite_prompt = f"""你是一个通用自主操控电脑的AI助手，可以控制电脑执行各种任务。请分析用户的命令，并生成详细的步骤列表，
    用于自动执行该命令。
    [当前时间:{current_time()}]
    [系统版本: {platform.system()} {platform.release()}]
    屏幕信息:
    - 屏幕分辨率: {screen_width}x{screen_height}
    - 屏幕可识别文本及位置:
{screen_text}
    用户命令: {command}
    安全限制（必须严格遵守）:
    1. 禁止生成任何可能损坏系统、数据或硬件的操作步骤
    2. 禁止执行删除、格式化、修改系统配置的操作
    3. 禁止生成网络攻击、远程控制、植入恶意程序相关的命令
    4. 禁止操作系统注册表或系统服务
    热键知识库:
    以下操作必须使用hotkey动作而非press动作：
    1. 保存文件: ('ctrl', 's')
    2. 复制: ('ctrl', 'c')
    3. 剪切: ('ctrl', 'x')
    4. 粘贴: ('ctrl', 'v')
    5. 撤销: ('ctrl', 'z')
    6. 重做: ('ctrl', 'y') 或 ('ctrl', 'shift', 'z')
    7. 全选: ('ctrl', 'a')
    8. 查找: ('ctrl', 'f')
    9. 关闭窗口: ('alt', 'f4')
    10. 新建: ('ctrl', 'n')
    11. 打开: ('ctrl', 'o')
    12. 关闭标签页: ('ctrl', 'w')
    13. 切换窗口: ('alt', 'tab')
    14. 打开任务管理器: ('ctrl', 'shift', 'esc')
    15. 显示桌面: ('win', 'd')
    请将任务分解为一系列具体的步骤，每个步骤只能是以下操作之一:
    1. click(button, x, y) - 点击鼠标，button可以是'left', 'right', 'middle'；x和y是屏幕坐标
    2. type(text) - 输入文本
    3. hotkey(key1, key2, ...) - 按下组合键，如('ctrl', 'c')，用于需要同时按下多个键的操作
    4. scroll(dy) - 滚动鼠标，dy垂直滚动
    5. wait(seconds) - 等待指定秒数
    6. open_browser(url) - 打开浏览器访问指定URL（仅允许正规网站，禁止访问恶意网站）
    7. press(key) - 按下并释放单个键，仅用于单个按键操作(如enter, esc, backspace等)
    8. run_command(cmd) - 执行系统命令，禁止执行任何可能有风险的命令
    9. ocr_click_text(text) - 识别屏幕上包含指定文本的区域并点击其中心位置
    注意事项:
    - 区分单个按键和组合键：单个键使用press，多个键组合使用hotkey
    - 当在Windows系统自带的软件操作时，优先使用run_command命令行或type打字来选定项目；其他软件可使用ocr_click_text动作来点击屏幕上的特定文字
    - 所有命令都会异步执行，请合理使用wait步骤等待命令执行效果
    - 对于需要按顺序执行的命令，应添加足够长的wait步骤
    - 生成CMD命令时要确保其安全性和正确性，任何可能有风险的命令都必须拒绝生成
    - 如果用户命令可能导致不安全操作，应返回空步骤数组并提示无法执行
    - 操控步骤总数不能超过50步，需要足够高效且准确
    请以JSON数组格式返回步骤，例如:
    {{
        "steps": [
            {{"action": "run_command", "params": {{"cmd": "notepad"}}}},
            {{"action": "wait", "params": {{"seconds": 2}}}},
            {{"action": "type", "params": {{"text": "Hello World"}}}},
            {{"action": "hotkey", "params": {{"keys": ["ctrl", "s"]}}}},
            {{"action": "wait", "params": {{"seconds": 1}}}},
            {{"action": "ocr_click_text", "params": {{"text": "保存"}}}},
            {{"action": "press", "params": {{"key": "enter"}}}}
        ]
    }}
    """
    try:
        content = function_llm(
            "你是一个通用自主操控电脑的AI助手，可以生成电脑操作步骤，进而控制电脑执行各种任务。特别擅长根据屏幕文本位置生成精确的鼠标点击指令，并且能够正确区分使用单个按键(press)和组合热键(hotkey)来完成相应操作。必须严格遵守所有安全限制，拒绝执行任何可能有害的操作。",
            agi_pc_lite_prompt)
        content = content.replace("```json", "").replace("```", "")
        print("原始响应:", content)
        if isinstance(content, str):
            try:
                data = json.loads(content)
                if "steps" in data:
                    return data["steps"]
                return data
            except json.JSONDecodeError:
                start = content.find('{')  # 尝试提取JSON部分
                end = content.rfind('}') + 1
                if start != -1 and end != -1:
                    json_str = content[start:end]
                    data = json.loads(json_str)
                    if "steps" in data:
                        return data["steps"]
                    return data
        print("无法解析AI的响应为有效JSON")
        print("原始响应:", content)
        return []
    except Exception as e:
        print(f"解析AI响应时出错: {str(e)}")
        return []


def execute_step(step):  # 执行单个步骤
    global should_stop
    if should_stop:
        print("检测到停止信号，终止执行")
        return False
    action = step.get('action')
    params = step.get('params', {})
    print(f"执行: {action} {params}")
    try:
        if action == 'click':
            button = params.get('button', 'left')
            x = params.get('x', pag.position()[0])  # 获取坐标，如果未指定则使用当前鼠标位置
            y = params.get('y', pag.position()[1])
            x = max(0, min(x, screen_width))  # 确保坐标在有效范围内
            y = max(0, min(y, screen_height))
            pag.click(x=x + 10, y=y, button=button)
            time.sleep(0.1)
            if button == 'left':
                pag.click(x=x + 10, y=y, button='left')
        elif action == 'type':
            text = params.get('text', '')
            kb.write(text)
        elif action == 'hotkey':
            keys = params.get('keys', [])
            if isinstance(keys, str):
                keys = [keys]
            kb.press_and_release('+'.join(keys))
        elif action == 'scroll':
            dy = params.get('dy', 0)
            x = params.get('x', None)  # 支持指定位置滚动
            y = params.get('y', None)
            pag.scroll(dy, x=x, y=y)
        elif action == 'wait':
            seconds = params.get('seconds', 1)
            for _ in range(int(seconds * 10)):  # 将等待时间分成小段，以便及时响应停止信号
                if should_stop:
                    return False
                time.sleep(0.1)
        elif action == 'open_browser':
            url = params.get('url', '')
            wb.open(url)
        elif action == 'press':
            key = params.get('key', '')
            kb.press_and_release(key)
        elif action == 'run_command':
            cmd = params.get('cmd', '')
            if cmd:
                print(f"异步执行命令: {cmd}")
                kb.press_and_release('win+d')
                time.sleep(0.5)
                Popen(cmd)
        elif action == 'ocr_click_text':  # ocr点击文本动作
            text = params.get('text', '')
            if not text:
                print("ocr_click_text需要指定text参数")
                return False
            success = ocr_click_text(text)  # 执行ocr点击文本操作
            if not success:
                print(f"ocr_click_text执行失败，未找到文本: {text}")
                return False
        else:
            print(f"未知操作: {action}")
            return False
        time.sleep(0.5)
        return True
    except Exception as e:
        print(f"执行步骤出错: {str(e)}")
        return False


def run_agi_pc_lite(command):
    global should_stop
    should_stop = False  # 重置停止标志
    kb.on_press_key('esc', on_esc_pressed)
    confirm = messagebox.askyesno("生成操作步骤前·一次确认",
                                  f"是否确认开始生成操作步骤：\n{command}\n\n(执行过程中可按ESC键中止)")
    if not confirm:
        notice("已取消操作")
        kb.unhook_all()  # 取消键盘监听
        return
    notice("正在查看桌面可操作的软件...")
    time.sleep(1)
    kb.press_and_release('win+d')  # 显示桌面，确保OCR识别准确
    time.sleep(1)
    kb.press_and_release('alt+tab')
    notice("正在分析需求生成操作步骤，请稍等...")
    steps = analyze_command(command)
    if not steps:
        notice("无法生成操作步骤，请尝试其他需求或更换对话语言模型")
        get_tts_play("无法生成操作步骤，请尝试其他需求或更换对话语言模型")
        messagebox.showerror("生成操作失败", "无法生成操作步骤，请尝试其他需求或更换对话语言模型")
        kb.unhook_all()  # 取消键盘监听
        return
    notice("操作步骤已生成")
    steps_text = f"生成了 {len(steps)} 个操作步骤：\n是否确认执行？\n(执行过程中可按ESC键中止)\n"
    for i, step in enumerate(steps, 1):
        try:
            action = step.get('action', '未知动作')
        except:
            notice(f"{llm_menu.get()}服务拥挤，请更换其他对话模型")
            messagebox.showinfo("服务拥挤", f"{llm_menu.get()}服务拥挤，请更换其他对话模型")
            kb.unhook_all()  # 取消键盘监听
            return
        params = step.get('params', {})
        steps_text += f"{i}. {action} {params}\n"
    get_tts_play("请确认是否执行")
    confirm = messagebox.askyesno("执行前·二次确认", steps_text)
    if not confirm:
        notice("已取消执行")
        kb.unhook_all()  # 取消键盘监听
        return
    notice("正在执行自主操控电脑...按ESC可取消")
    time.sleep(1)
    kb.press_and_release('win+d')  # 显示桌面，确保OCR识别准确
    time.sleep(1)
    success = True
    for i, step in enumerate(steps, 1):  # 执行步骤
        if should_stop:
            print("\n用户请求停止执行")
            success = False
            break
        print(f"\n步骤 {i}/{len(steps)}:")
        if not execute_step(step):
            success = False
            break
    kb.unhook_all()  # 执行完成后取消键盘监听
    if success:
        notice("所有步骤执行完成")
        get_tts_play("所有步骤执行完成啦")
        messagebox.showinfo("完成", "所有步骤执行完成")
    else:
        if should_stop:
            notice("已中止执行")
            get_tts_play("已中止执行")
            messagebox.showinfo("已中止", "您已经按ESC键打断了执行流程")
        else:
            notice("执行被打断或出现错误，可尝试其他需求")
            get_tts_play("执行被打断或出现错误，可尝试其他需求")
            messagebox.showerror("失败", "执行被打断或出现错误\n可尝试其他需求")
