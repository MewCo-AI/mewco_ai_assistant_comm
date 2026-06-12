import pyautogui as pag
import requests as rq
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QMainWindow, QMenu, QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QVBoxLayout
from sys_init import *

FixedSize_x, FixedSize_y, ZoomFactor = 200, 350, 0.55
screen_width, screen_height = pag.size()


class WebMenu(QMenu):
    def __init__(self):
        super(WebMenu, self).__init__()
        self.chat_act = QAction("💬 便捷聊天")
        self.show_border_act = QAction("👐 拖动桌宠")
        self.hide_border_act = QAction("🌫 隐藏边框")
        self.reload_act = QAction("🔄 重新加载")
        self.exit_act = QAction("✖️ 关闭桌宠")
        self.addAction(self.chat_act)
        self.addAction(self.show_border_act)
        self.addAction(self.hide_border_act)
        self.addAction(self.reload_act)
        self.addAction(self.exit_act)


class ChatWidget(QWidget):
    def __init__(self, parent=None, is_input=True, message=""):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint |
                            Qt.WindowType.WindowStaysOnTopHint |
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("""QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: rgba(0, 127, 255, 0.9);
                color: white;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(0, 200, 255, 1.0);
            }
            QLabel {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #cccccc;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                max-width: 200px;
            }""")
        if is_input:
            layout = QHBoxLayout()
            layout.setContentsMargins(5, 5, 5, 5)
            self.input_field = QLineEdit()
            self.input_field.setPlaceholderText("请输入消息...")
            self.send_btn = QPushButton("📤")
            self.send_btn.setFixedSize(30, 30)
            layout.addWidget(self.input_field, 1)
            layout.addWidget(self.send_btn)
            self.setLayout(layout)
            self.send_btn.clicked.connect(self.send_message)
            self.input_field.returnPressed.connect(self.send_message)
        else:
            layout = QVBoxLayout()
            layout.setContentsMargins(5, 5, 5, 5)
            self.message_label = QLabel(message)
            self.message_label.setWordWrap(True)
            layout.addWidget(self.message_label)
            self.setLayout(layout)

    def send_message(self):
        text = self.input_field.text().strip()
        if text:
            parent = self.parent()
            if parent and hasattr(parent, 'handle_chat_message'):
                parent.handle_chat_message(text)
        self.close()


class Live2dPet(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        if pet_top_switch == "开启":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        self.setWindowTitle("桌宠 - 枫云AI助手社区版")
        self.setWindowIcon(QIcon('data/image/logo.png'))
        self.pet_browser = QWebEngineView()
        self.setCentralWidget(self.pet_browser)
        self.resize(FixedSize_x, FixedSize_y)
        self.web_menu = WebMenu()
        self.pet_browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.pet_browser.customContextMenuRequested.connect(self.show_context_menu)
        self.pet_browser.load(f'http://127.0.0.1:{live2d_port}/pet')
        self.pet_browser.page().setBackgroundColor(Qt.GlobalColor.transparent)
        self.pet_browser.setZoomFactor(ZoomFactor)
        self.move(pet_x, pet_y)
        self.web_menu.reload_act.triggered.connect(self.reload_page)
        self.web_menu.exit_act.triggered.connect(self.close)
        self.web_menu.show_border_act.triggered.connect(self.show_border)
        self.web_menu.hide_border_act.triggered.connect(self.hide_border)
        self.web_menu.chat_act.triggered.connect(self.show_chat_input)
        self.thinking_label = None

    def zoom_in_pet(self):
        global FixedSize_x, FixedSize_y, ZoomFactor
        FixedSize_x = FixedSize_x * 1.1
        FixedSize_y = FixedSize_y * 1.1
        ZoomFactor = ZoomFactor * 1.1
        self.resize(int(FixedSize_x), int(FixedSize_y))
        self.pet_browser.setZoomFactor(ZoomFactor)

    def zoom_out_pet(self):
        global FixedSize_x, FixedSize_y, ZoomFactor
        FixedSize_x = FixedSize_x * 0.9
        FixedSize_y = FixedSize_y * 0.9
        ZoomFactor = ZoomFactor * 0.9
        self.resize(int(FixedSize_x), int(FixedSize_y))
        self.pet_browser.setZoomFactor(ZoomFactor)

    def show_context_menu(self, pos):
        self.web_menu.exec(self.pet_browser.mapToGlobal(pos))

    def reload_page(self):
        self.pet_browser.reload()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in_pet()
        else:
            self.zoom_out_pet()

    def show_border(self):
        self.setWindowFlags(Qt.WindowType.WindowMinimizeButtonHint)
        if pet_top_switch == "开启":
            self.setWindowFlags(Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def hide_border(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowMinimizeButtonHint)
        if pet_top_switch == "开启":
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def show_chat_input(self):
        self.chat_input = ChatWidget(parent=self)
        x = self.x() + int(self.width() / 1.5)
        y = self.y()
        self.chat_input.move(x, y)
        self.chat_input.show()
        self.chat_input.input_field.setFocus()

    def show_thinking_label(self):
        if self.thinking_label:
            self.thinking_label.close()
        self.thinking_label = ChatWidget(parent=self, is_input=False, message=f"{asst_name}正在思考中...")
        x = self.x() + int(self.width() / 1.5)
        y = self.y()
        self.thinking_label.move(x, y)
        self.thinking_label.show()

    def hide_thinking_label(self):
        if self.thinking_label:
            self.thinking_label.close()
            self.thinking_label = None

    def handle_chat_message(self, message):
        self.show_thinking_label()
        QTimer.singleShot(100, lambda: self.send_chat_request(message))

    def send_chat_request(self, message):
        try:
            response = rq.get("http://127.0.0.1:5249/pet_chat",
                              params={"msg": message, "key": "mewcopetchat"})
            if response.status_code == 200:
                data = response.json()
                answer = data["answer"]
            else:
                error_data = response.json()
                answer = error_data["error"]
        except Exception as e:
            answer = f"发生错误，详情：{e}"
        self.hide_thinking_label()
        if pet_subtitle_switch == "开启":
            self.show_chat_response(answer)
            wait_time = len(answer) * 250
            if wait_time > 30000:
                wait_time = 30000
            QTimer.singleShot(wait_time, self.chat_response.close)

    def show_chat_response(self, response):
        self.chat_response = ChatWidget(parent=self, is_input=False, message=response)
        x = self.x() + int(self.width() / 1.5)
        y = self.y()
        self.chat_response.move(x, y)
        self.chat_response.show()
