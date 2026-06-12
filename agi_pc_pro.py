import subprocess
import pyperclip
from pydantic import BaseModel
from agi_pc_lite import *

should_exit = False  # 全局退出标志
input_path = "data/cache/cache_screen.png"
output_path = "data/cache/screen_label.png"
max_png = 1280
move_duration = 0.1
pag.FAILSAFE = False

agi_pc_prompt = """
你是一个 GUI 代理，负责控制鼠标/键盘自动化系统。你的任务是分析当前屏幕状态和用户指令，然后确定完成任务所需的**唯一下一个操作**。系统每次只能执行一个操作（一次鼠标移动/点击或一次键盘输入），因此你必须只关注当前立即需要执行的操作。

## 核心约束

1. **单步聚焦**：仅输出下一步的即时操作，绝不规划多个步骤  
2. **仅基于截图**：所有决策必须严格基于提供的截图内容，不得推测或虚构屏幕外的元素  
3. **90 步限制**：若任务无法在 90 次迭代内完成，返回 "difficult"  
4. **禁止支付操作**：一旦检测到任何支付/结账页面，立即中止（返回 "difficult"）  
5. **通话礼仪**：切勿主动挂断通话；只有在用户明确要求时才点击挂断按钮  
6. **错误纠正**：若发现历史操作有误（如选错联系人、发错消息等），应在下一步中修正。所有的操作要以图片中显示的内容为主，以历史信息为副 来做决定。当发现图片中与历史信息不符，以图片为准。  
7. **内容覆盖**：当发现需要在输入框中重新输入内容覆盖掉原来内容时，就先点击到该输入框区域，然后全选该输入框中的内容，然后按delete键删除原来的内容，然后再写入新内容。

## 输出格式（严格 JSON）

{
  "current_status": "对当前屏幕状态的简洁描述",
  "whether_completed": "True|False|difficult",
  "element_info": "明确无歧义的元素描述，或“页面正在加载”",
  "coordinates": "[x, y] 或拖拽操作用 [[x1, y1], [x2, y2]]",
  "action": "click|double_click|long_press|right_click|drag|scroll_up|scroll_down|hotkey|page_loading|run_command",
  "type_information": "要输入的文本、快捷键组合，或空字符串"
}

### 字段说明

**current_status**：简要描述当前状态（例如："联系人缺失"、"对话中"、"视频播放中"）

**whether_completed**：根据**屏幕可见内容**进行关键判断  
- `"True"`：任务已在屏幕上明显完成（例如：消息已发送并显示、通话已接通、视频已点赞）  
- `"False"`：任务尚未完成，仍需下一步操作  
- `"difficult"`：任务过于复杂、出现支付页面、需要登录，或操作不可行  

**element_info**：  
- 必须明确无歧义，例如："微信联系人列表中‘张三’的头像"，而非"顶部头像"  
- 若页面正在加载，必须明确写为"页面正在加载"

**coordinates**：  
- 单点操作：`[x, y]`（元素中心坐标）  
- 拖拽操作：`[[x1, y1], [x2, y2]]`（起点与终点）  
- 页面加载 / whether_completed 为 True 或 difficult 时：`[0, 0]`  
- **run_command** 操作时：`[0, 0]`

**action**：仅限以下枚举值  
- `click`：单次左键点击  
- `double_click`：双击左键  
- `long_press`：长按  
- `right_click`：右键（打开上下文菜单）  
- `drag`：从起点拖拽至终点  
- `scroll_up` / `scroll_down`：在指定位置滚动滚轮  
- `hotkey`：执行键盘快捷键  
- `page_loading`：页面正在加载（系统将自动暂停 0.5 秒）  
- `run_command`：直接执行系统级 CMD 命令。使用 type_information 字段传递命令字符串

**type_information**：  
- 文本输入：要键入的内容（用 `\n` 表示回车）  
- 快捷键：以空格分隔的按键（例如："ctrl c"，最多 3 个键）  
- **CMD命令**：当 action 为 `run_command` 时，此处填写要执行的命令（例如："notepad", "calc", "mspaint"）。**注意：此操作不涉及鼠标坐标，系统将直接在后台执行该命令。**  
- 其他情况：空字符串

## 操作类型详情

| 操作 | 坐标格式 | type_information | 说明 |
|------|----------|------------------|------|
| `click` | `[x, y]` | 可选文本 | 左键点击元素，可选择在点击后输入文本 |
| `double_click` | `[x, y]` | 空 | 双击元素 |
| `long_press` | `[x, y]` | 空 | 长按元素 |
| `right_click` | `[x, y]` | 空 | 右键点击，弹出上下文菜单 |
| `drag` | `[[x1,y1],[x2,y2]]` | 空 | 从起点拖拽到终点 |
| `scroll_up/down` | `[x, y]` | 空 | 在指定位置向上/向下滚动 |
| `hotkey` | `[x, y]` | "ctrl a" | 执行快捷键（最多 3 个键） |
| `page_loading` | `[0, 0]` | 空 | 检测到页面加载，自动暂停 |
| `run_command` | `[0, 0]` | "notepad" | 执行系统CMD命令 |

## 操作逻辑讲解
操作逻辑以鼠标与键盘协同为核心：**单击**选中或激活，**双击**打开文件/文件夹/软件，**右键**呼出菜单执行复制、删除、属性等操作，**长按拖拽**可移动文件；打开软件可双击桌面图标、单击任务栏固定项、开始菜单搜索或按Win+R运行命令；删除文件按Delete进回收站，支持Ctrl+单击多选和框选批量操作，核心快捷键Ctrl+C/V复制粘贴、Ctrl+Z撤销、Win+D返回桌面、Win+S全局搜索贯穿始终。
特别强调：当画面处于桌面时，打开桌面图标务必使用双击操作。
还可根据实际情况进行其他操作。

### CMD 命令支持说明
除了常规的鼠标键盘操作，你现在具备了直接调用系统命令的能力。当用户要求打开特定的系统工具（如记事本、计算器、画图、任务管理器、系统设置等）时，优先使用 `run_command` 动作。
示例：
- 打开记事本: `{"action": "run_command", "type_information": "notepad", "coordinates": [0, 0]}`
- 打开计算器: `{"action": "run_command", "type_information": "calc", "coordinates": [0, 0]}`
- 打开画图: `{"action": "run_command", "type_information": "mspaint", "coordinates": [0, 0]}`

## 特殊处理规则

**页面加载检测**：当观察到加载动画、进度条、旋转图标或内容正在变化时：  
- `element_info` 设为 “页面正在加载”  
- `action` 设为 “page_loading”  
- `coordinates` 设为 `[0, 0]`  
- `type_information` 为空字符串  

**支付页面**：任何结账、支付或订单确认页面 → 立即返回 `"difficult"`

**通话场景**：  
- 若用户要求呼叫“张三”，而屏幕已显示与“张三”的通话中 → 返回 `"True"`（已接通）  
- 除非用户明确要求，否则不得点击挂断按钮  

**错误纠正**：若操作历史显示选错联系人、发错消息等，应在下一步中立即纠正。所有的操作要以图片中显示的内容为主，以历史信息为副 来做决定。当发现图片中与历史信息不符，以图片为准。  

**中断机制**：若用户按下 **Esc** 键，程序将立即停止当前所有操作并退出。请务必在任务完成或无法完成时返回正确的状态。

## 示例场景

### 消息发送场景
// 示例 1：选错联系人
{
  "current_status": "当前是与'李四'的聊天页面，非目标联系人",
  "whether_completed": "False",
  "element_info": "微信搜索框（左上角放大镜图标）",
  "coordinates": [278, 130],
  "action": "click",
  "type_information": "张三"
}

// 示例 2：进入正确聊天窗口，准备输入
{
  "current_status": "当前是与'张三'的聊天页面",
  "whether_completed": "False",
  "element_info": "聊天输入框（窗口底部）",
  "coordinates": [795, 748],
  "action": "click",
  "type_information": "晚上好\n"
}

// 示例 3：消息已成功发送
{
  "current_status": "消息已发送并显示在聊天窗口",
  "whether_completed": "True",
  "element_info": "",
  "coordinates": [0, 0],
  "action": "",
  "type_information": ""
}

### 媒体交互
// 示例 4：点赞视频
{
  "current_status": "抖音视频播放中",
  "whether_completed": "False",
  "element_info": "右侧点赞按钮（心形图标）",
  "coordinates": [1100, 500],
  "action": "click",
  "type_information": ""
}

// 示例 5：滚动查找内容
{
  "current_status": "哔哩哔哩个人主页，需滚动查找2024年12月视频",
  "whether_completed": "False",
  "element_info": "视频列表区域",
  "coordinates": [900, 500],
  "action": "scroll_down",
  "type_information": ""
}

### 高级操作
// 示例 6：右键打开上下文菜单
{
  "current_status": "桌面界面，准备复制文件夹",
  "whether_completed": "False",
  "element_info": "桌面上的'文档'文件夹图标",
  "coordinates": [300, 400],
  "action": "right_click",
  "type_information": ""
}

// 示例 7：拖拽文件
{
  "current_status": "桌面界面，准备移动文件",
  "whether_completed": "False",
  "element_info": "桌面上的'temp.txt'文件图标",
  "coordinates": [[200, 300], [1800, 900]],
  "action": "drag",
  "type_information": ""
}

// 示例 8：快捷键操作
{
  "current_status": "文档编辑页，准备全选复制",
  "whether_completed": "False",
  "element_info": "文档编辑区域",
  "coordinates": [500, 400],
  "action": "hotkey",
  "type_information": "ctrl a"
}

// 示例 9：返回桌面
{
  "current_status": "在浏览器界面，准备返回桌面",
  "whether_completed": "False",
  "element_info": "无（执行快捷键操作返回桌面）",
  "coordinates": [0, 0],
  "action": "hotkey",
  "type_information": "win d"
}

### CMD 命令场景
// 示例 10：打开记事本
{
  "current_status": "用户请求打开记事本",
  "whether_completed": "False",
  "element_info": "无",
  "coordinates": [0, 0],
  "action": "run_command",
  "type_information": "notepad"
}

// 示例 11：打开计算器
{
  "current_status": "用户请求打开计算器",
  "whether_completed": "False",
  "element_info": "无",
  "coordinates": [0, 0],
  "action": "run_command",
  "type_information": "calc"
}

### 特殊状态
// 示例 12：页面加载中
{
  "current_status": "页面正在加载中",
  "whether_completed": "False",
  "element_info": "页面正在加载",
  "coordinates": [0, 0],
  "action": "page_loading",
  "type_information": ""
}

// 示例 13：检测到支付页面
{
  "current_status": "检测到支付页面，禁止操作",
  "whether_completed": "difficult",
  "element_info": "",
  "coordinates": [0, 0],
  "action": "",
  "type_information": ""
}

---

**请牢记**：你的唯一职责是分析当前截图，并输出**一个精确的下一步操作**。务必果断、准确，绝不做出超出屏幕可见内容的假设。
"""


def on_esc_press(e):
    global should_exit
    if e.event_type == kb.KEY_DOWN and e.name == 'esc':
        should_exit = True
        print("\n检测到ESC键按下，正在停止操作...")


def capture_screen_and_save():
    output_dir = os.path.dirname(input_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    screenshot = pag.screenshot()
    screenshot_np = np.array(screenshot)
    screenshot_bgr = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    scale = 1
    height, width, _ = screenshot_bgr.shape
    max_edge = max(height, width)
    if max_edge > max_png:
        scale = max_png / max_edge
        screenshot_bgr = cv2.resize(screenshot_bgr, None, fx=scale, fy=scale)
    save_params = [int(cv2.IMWRITE_PNG_COMPRESSION), 1]
    cv2.imwrite(input_path, screenshot_bgr, save_params)
    return scale


def mark_coordinate_on_image(coordinates, output_path2, point_radius=10, point_color=(0, 0, 255), thickness=-1):
    if not os.path.exists(input_path):
        return False
    image = cv2.imread(input_path)
    if image is None:
        return False
    img_height, img_width = image.shape[:2]
    points_to_mark = []
    if isinstance(coordinates[0], list) or isinstance(coordinates[0], tuple):
        for coord in coordinates:
            if isinstance(coord, (list, tuple)) and len(coord) == 2:
                x, y = int(coord[0]), int(coord[1])
                if 0 <= x < img_width and 0 <= y < img_height:
                    points_to_mark.append((x, y))
    else:
        if len(coordinates) == 2:
            x, y = int(coordinates[0]), int(coordinates[1])
            if 0 <= x < img_width and 0 <= y < img_height:
                points_to_mark.append((x, y))
    if not points_to_mark:
        return False
    for i, (x, y) in enumerate(points_to_mark):
        cv2.circle(image, (x, y), point_radius, point_color, thickness)
        text = f"P{i + 1} ({x}, {y})" if len(points_to_mark) > 1 else f"({x}, {y})"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (0, 0, 255)
        font_thickness = 2
        offset = i * 40
        text_position = (x - 30 + offset, y - 20)
        cv2.putText(image, text, text_position, font, font_scale, font_color, font_thickness)
    output_dir = os.path.dirname(output_path2)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    save_params = [int(cv2.IMWRITE_PNG_COMPRESSION), 1]
    cv2.imwrite(output_path2, image, save_params)
    return True


def map_coordinates(x, y, scale, img_width=None, img_height=None):
    x = max(-100000, min(100000, x))
    y = max(-100000, min(100000, y))
    if img_width and img_height:
        x_abs = (x / 1000) * img_width
        y_abs = (y / 1000) * img_height
    else:
        x_abs = x
        y_abs = y
    x_r = x_abs / scale
    y_r = y_abs / scale
    x_r = max(0, min(100000, x_r))
    y_r = max(0, min(100000, y_r))
    return x_r, y_r


class MathResponse(BaseModel):
    current_status: str
    whether_completed: str
    element_info: str
    coordinates: list
    action: str
    type_information: str


def get_next_element(user_content):
    def read_local_image(image_path):
        img = cv2.imread(image_path)
        if img is None:
            raise Exception(f"无法读取图片: {image_path}")
        height, width, channels = img.shape
        print(f"成功读取图片: {image_path}，图片尺寸: {width} x {height} 像素")
        _, buffer = cv2.imencode('.jpg', img)
        img_base64 = b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{img_base64}"

    if not os.path.exists(input_path):
        error_msg = f"错误：图片文件不存在 - {os.path.abspath(input_path)}"
        print(error_msg)
        root.after(0, lambda: messagebox.showerror("执行错误", error_msg))
        return None
    try:
        image_data_url = read_local_image(input_path)
        print("\n正在调用多模态大模型分析图片...")
        messages = [{"role": "system", "content": agi_pc_prompt},
                    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_data_url}},
                                                 {"type": "text", "text": user_content}]}]
        client = OpenAI(api_key=agi_pc_pro_api_key, base_url=agi_pc_pro_base_url)
        completion = client.beta.chat.completions.parse(
            model=agi_pc_pro_vlm_model, messages=messages, response_format=MathResponse,
            extra_body={"thinking": {"type": "disabled"}, "enable_thinking": False})
        print(completion.choices[0].message.content)
        return completion.choices[0].message.content
    except Exception as e:
        error_msg = f"多模态模型调用失败，错误详情: {str(e)}"
        print(error_msg)
        root.after(0, lambda: messagebox.showerror("执行错误", error_msg))
        return None


def parse_json(json_str):
    try:
        if json_str.startswith('```json'):
            json_str = json_str[7:]
        if json_str.endswith('```'):
            json_str = json_str[:-3]
        json_str = json_str.strip()
        json_pattern = r'\{\s*"(?:[^"\\]|\\.)*"\s*:\s*(?:"(?:[^"\\]|\\.)*"|\d+\.?\d*|true|false|null|\[.*?\]|\{.*?\})\s*(?:,\s*"(?:[^"\\]|\\.)*"\s*:\s*(?:"(?:[^"\\]|\\.)*"|\d+\.?\d*|true|false|null|\[.*?\]|\{.*?\})\s*)*\}'
        json_matches = re.findall(json_pattern, json_str, re.DOTALL)
        if json_matches:
            valid_json = max(json_matches, key=len)
            print(f"从AI输出中提取的JSON: {valid_json}")
            return json.loads(str(valid_json))
        else:
            first_brace = json_str.find('{')
            last_brace = json_str.rfind('}')
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                valid_json = json_str[first_brace:last_brace + 1]
                print(f"提取的有效JSON: {valid_json}")
                return json.loads(valid_json)
            else:
                return json.loads(json_str)
    except json.JSONDecodeError as e:
        error_msg = f"JSON解析错误: {e}"
        print(error_msg)
        try:
            cleaned_str = re.sub(r'^\s*{\s*{\s*', '{', json_str)
            cleaned_str = re.sub(r'\s*}\s*}\s*$', '}', cleaned_str)
            print(f"清理后的JSON: {cleaned_str}")
            return json.loads(cleaned_str)
        except json.JSONDecodeError as e:
            error_msg2 = f"二次解析失败: {e}"
            print(error_msg2)
            root.after(0, lambda: messagebox.showerror("执行错误", f"{error_msg}\n{error_msg2}"))
            return None


def move_mouse_to_coordinates(coordinates, action, type_information, scale=1):
    global should_exit
    action_str = ""
    if should_exit:
        return "操作已被用户终止"
    if action == "page_loading":
        print("检测到页面正在加载，暂停3秒...")
        action_str = "检测到页面正在加载，暂停3秒..." + "\n"
        time.sleep(3)
        print("暂停结束，继续操作")
        action_str = action_str + "暂停结束，继续操作" + "\n"
        return action_str
    if action == "run_command":
        cmd = type_information
        if cmd:
            print(f"正在执行系统命令: {cmd}")
            action_str = f"正在执行系统命令: {cmd}" + "\n"
            subprocess.Popen(cmd, shell=True)
            print(f"命令已发送: {cmd}")
        return action_str
    img = cv2.imread(input_path)
    img_height, img_width, _ = img.shape if img is not None else (None, None, None)
    if action == "hotkey":
        if type_information:
            keys = type_information.split()
            keys = ["win" if key == "meta" else key for key in keys]
            print(f"执行热键操作: {'+'.join(keys)}")
            pag.hotkey(*keys)
            action_str = f"执行热键操作: {'+'.join(keys)}" + "\n"
        else:
            print("热键操作但未提供快捷键信息")
        return action_str
    if action == "drag" and isinstance(coordinates[0], list):
        start_x, start_y = coordinates[0]
        end_x, end_y = coordinates[1]
        start_x, start_y = map_coordinates(start_x, start_y, scale, img_width, img_height)
        end_x, end_y = map_coordinates(end_x, end_y, scale, img_width, img_height)
        pag.moveTo(start_x, start_y, duration=float(move_duration))
        print(f"鼠标已移动到拖拽起点: ({start_x}, {start_y})")
        action_str = f"鼠标已移动到拖拽起点: ({start_x}, {start_y})" + "\n"
        pag.dragTo(end_x, end_y, duration=float(move_duration) * 10)
        print(f"已完成拖拽操作: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
        action_str = action_str + f"已完成拖拽操作: ({start_x}, {start_y}) -> ({end_x}, {end_y})" + "\n"
    else:
        x, y = coordinates
        x, y = map_coordinates(x, y, scale, img_width, img_height)
        pag.moveTo(x, y, duration=float(move_duration))
        print(f"鼠标已移动到坐标: ({x}, {y})")
        action_str = f"鼠标已移动到坐标: ({x}, {y})" + "\n"
        if action == "click":
            pag.click()
            print(f"已点击 ({x}, {y})")
            action_str = action_str + f"已点击 ({x}, {y})" + "\n"
        elif action == "double_click":
            pag.doubleClick()
            print(f"已双击 ({x}, {y})")
            action_str = action_str + f"已双击 ({x}, {y})" + "\n"
        elif action == "long_press":
            pag.mouseDown()
            print(f"已长按 ({x}, {y})")
            action_str = action_str + f"已长按 ({x}, {y})" + "\n"
        elif action == "right_click":
            pag.rightClick()
            print(f"已右键点击 ({x}, {y})")
            action_str = action_str + f"已右键点击 ({x}, {y})" + "\n"
        elif action == "scroll_up":
            pag.scroll(500)
            print(f"已向上滚动 ({x}, {y})")
            action_str = action_str + f"已向上滚动 ({x}, {y})" + "\n"
        elif action == "scroll_down":
            pag.scroll(-500)
            print(f"已向下滚动 ({x}, {y})")
            action_str = action_str + f"已向下滚动 ({x}, {y})" + "\n"
        else:
            print(f"未知操作: {action}")
            root.after(0, lambda: messagebox.showerror("执行错误", f"未知操作类型: {action}"))
    time.sleep(0.5)
    if type_information != "" and action != "hotkey" and action != "run_command":
        pyperclip.copy(type_information)
        pag.hotkey('ctrl', 'v')
        print(f"已粘贴: {type_information}")
        time.sleep(0.5)
        pag.press('enter')
        time.sleep(0.5)
        print("已发送")
        action_str = action_str + f"已发送: {type_information}" + "\n"
    pag.moveTo(0, 0, duration=float(move_duration))
    time.sleep(1.5)
    return action_str


def run_agi_pc_pro(user_input):
    global should_exit
    should_exit = False
    notice("请确认是否执行")
    get_tts_play("请确认是否执行")
    confirm = messagebox.askyesno("执行前确认",
                                  f"是否确认执行以下任务？\n\n{user_input}\n\n(执行过程中按ESC键可随时中止)")
    if not confirm:
        messagebox.showinfo("操作取消", "您已取消执行该任务！")
        return "任务已被用户取消"
    notice("正在执行自主操控电脑...按ESC可取消")
    kb.hook(on_esc_press)
    print("ESC键监听已设置，按ESC可随时退出程序")
    try:
        time.sleep(3)
        time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        user_content = "当前时间为:" + time_str + "\n" + "用户任务为:" + user_input
        print(f"正在处理：{user_input}...")
        before_output = []
        current_status = "未完成"
        recent_coordinates = []
        same_coordinate_count = 0
        label_dir = os.path.dirname(output_path)
        if os.path.exists(label_dir):
            for filename in os.listdir(label_dir):
                if filename.startswith("cache_screen_label") and filename.endswith(".png"):
                    file_path = os.path.join(label_dir, filename)
                    os.remove(file_path)
            print(f"已清空label文件夹: {label_dir}")
        next_element = None
        action_str = ""
        execute_success = True
        for i in range(92):
            if should_exit:
                print("检测到退出标志，停止循环...")
                execute_success = False
                break
            print("\n" + f"=================第 {i} 次循环===============" + "\n")
            if i == 0:
                before_output = []
                before_content = ""
            else:
                before_output.append(str(next_element))
                if len(before_output) > 10:
                    before_output.pop(0)
                before_output_str = "".join(before_output)
                before_content = "之前的AI输出操作为: " + before_output_str + "\n" + "之前已完成的操作为:" + action_str
            try:
                scale = capture_screen_and_save()
                print(f"屏幕截图已保存为 {os.path.basename(input_path)}")
                next_element = get_next_element(before_content + "\n" + user_content)
                if not next_element:
                    error_msg = "未获取到模型返回的下一步操作"
                    print(error_msg)
                    root.after(0, lambda: messagebox.showerror("执行错误", error_msg))
                    execute_success = False
                    break
                next_element = parse_json(next_element)
                if not next_element:
                    error_msg = "解析模型返回的JSON失败"
                    print(error_msg)
                    root.after(0, lambda: messagebox.showerror("执行错误", error_msg))
                    execute_success = False
                    break
                current_status = next_element.get('current_status', '未知状态')
                whether_completed = next_element.get('whether_completed', 'difficult')
                element_info = next_element.get('element_info', '未知元素')
                coordinates = next_element.get('coordinates', [0, 0])
                action = next_element.get('action', '未知操作')
                type_information = next_element.get('type_information', '')
                if whether_completed == "True":
                    print(f"任务完成：{current_status}")
                    break
                if whether_completed == "difficult":
                    print(f"任务无法完成：{current_status}")
                    root.after(0, lambda: messagebox.showerror("执行失败", f"任务无法完成：{current_status}"))
                    execute_success = False
                    break
                print(f"下一步应该点击的元素: {element_info}")
                coordinates_match = False
                for coord in recent_coordinates:
                    if coord[0] == coordinates[0] and coord[1] == coordinates[1]:
                        coordinates_match = True
                        break
                if not coordinates_match:
                    recent_coordinates.append(coordinates.copy())
                    same_coordinate_count = 1
                    if len(recent_coordinates) > 3:
                        recent_coordinates.pop(0)
                else:
                    same_coordinate_count += 1
                if same_coordinate_count >= 3:
                    print("检测到连续3次相同坐标，清空记忆")
                    before_output = []
                    same_coordinate_count = 0
                    recent_coordinates = []
                action_str = move_mouse_to_coordinates(coordinates, action, type_information, scale=scale)
                output_filename = f"cache_screen_label{i + 1}.png"
                output_path2 = os.path.join(os.path.dirname(output_path), output_filename)
                mark_coordinate_on_image(coordinates, output_path2)
            except Exception as e:
                error_msg = f"执行第{i}次循环时出错: {str(e)}"
                print(error_msg)
                root.after(0, lambda: messagebox.showerror("执行错误", error_msg))
                execute_success = False
                break
        if execute_success:
            if should_exit:
                notice("已中止执行")
                get_tts_play("已中止执行")
                messagebox.showinfo("执行中止", "您已按下ESC键，操作已中止！")
            elif whether_completed == "True":
                notice("任务执行完成")
                get_tts_play("任务执行完成啦")
                messagebox.showinfo("执行完成", f"任务已成功完成！\n\n状态：{current_status}")
            else:
                notice("已达到90步操作上限，任务执行结束")
                get_tts_play("已达到90步操作上限，任务执行结束")
                messagebox.showwarning("执行结束", "已达到90步操作上限，任务执行结束！")
        else:
            if should_exit:
                notice("已中止执行")
                get_tts_play("已中止执行")
                messagebox.showinfo("执行中止", "您已按下ESC键，操作已中止！")
            else:
                notice("执行失败，可尝试其他需求")
                get_tts_play("执行失败，可尝试其他需求")
                messagebox.showerror("执行失败", "操作过程中出现错误，任务执行失败！")
        return current_status
    except Exception as e:
        error_msg = f"程序执行异常: {str(e)}"
        print(error_msg)
        root.after(0, lambda: messagebox.showerror("执行错误", error_msg))
        return error_msg
    finally:
        kb.unhook_all()
        print("已取消键盘监听")
