from main_sub import *


def run_dingding():
    import dingtalk_stream as dingding
    class DingChatBotHandler(dingding.ChatbotHandler):
        def __init__(self):
            super(dingding.ChatbotHandler, self).__init__()

        async def process(self, callback: dingding.CallbackMessage):
            try:
                incoming_message = dingding.ChatbotMessage.from_dict(callback.data)
                user_input = incoming_message.text.content.strip()
                print(f"钉钉收到用户消息：{user_input}")
                if im_run_mode_permission == "仅聊天(推荐)":
                    reply_content = chat_preprocess(user_input)
                else:
                    reply_content = common_chat(user_input)
                if reply_content is None:
                    reply_content = "OK"
                print(f"钉钉回复用户消息：{reply_content}")
                self.reply_text(reply_content, incoming_message)
            except Exception as e2:
                print(f"钉钉处理消息错误：{e2}")
            return dingding.AckMessage.STATUS_OK, 'OK'

    try:
        dingding_credential = dingding.Credential(dingding_client_id, dingding_client_secret)
        dingding_client = dingding.DingTalkStreamClient(dingding_credential)
        dingding_client.register_callback_handler(dingding.chatbot.ChatbotMessage.TOPIC, DingChatBotHandler())
        print("钉钉机器人已启动，等待接收消息...")
        dingding_client.start_forever()
    except Exception as e3:
        print(f"钉钉Stream客户端异常：{e3}")


def run_feishu():
    import lark_oapi as lark
    from lark_oapi.api.im.v1 import CreateMessageRequest, CreateMessageRequestBody

    def feishu_bot_handle(data: lark.im.v1.P2ImMessageReceiveV1) -> None:
        try:
            event = data.event
            message = event.message
            if message.message_type != "text":
                return
            content_json = message.content
            content_dict = json.loads(content_json)
            text_content = content_dict.get("text", "").strip()
            sender = event.sender
            open_id = sender.sender_id.open_id if sender.sender_id else "unknown"
            print(f"飞书收到用户消息：{text_content}")
            if im_run_mode_permission == "仅聊天(推荐)":
                reply_text = chat_preprocess(text_content)
            else:
                reply_text = common_chat(text_content)
            if reply_text is None:
                reply_text = "OK"
            send_reply_feishu(open_id, reply_text)
        except Exception as e2:
            print(f"飞书处理消息错误：{e2}")

    def send_reply_feishu(open_id: str, text: str) -> None:
        try:
            client = lark.Client.builder().app_id(feishu_app_id).app_secret(feishu_app_secret).build()
            req = CreateMessageRequest.builder().receive_id_type("open_id").request_body(
                CreateMessageRequestBody.builder().receive_id(open_id).msg_type("text").content(
                    json.dumps({"text": text})).build()).build()
            client.im.v1.message.create(req)
            print(f"飞书回复用户消息：{text}")
        except Exception as e2:
            print(f"飞书发送消息异常：{e2}")

    try:
        event_handler = lark.EventDispatcherHandler.builder("", "").register_p2_im_message_receive_v1(
            feishu_bot_handle).build()
        cli = lark.ws.Client(feishu_app_id, feishu_app_secret, event_handler=event_handler)
        print("飞书机器人已启动，等待接收消息...")
        cli.start()
    except Exception as e3:
        print(f"飞书Stream客户端异常：{e3}")


def run_qqbot():
    import botpy
    from botpy.message import C2CMessage
    logging.getLogger("botpy").setLevel(logging.WARNING)
    class QBotClient(botpy.Client):
        async def on_c2c_message_create(self, message: C2CMessage):
            input_msg = message.content
            print(f"收到QQ私聊消息：{message.author.user_openid} -> {input_msg}")
            if im_run_mode_permission == "仅聊天(推荐)":
                answer = chat_preprocess(input_msg)
            else:
                answer = common_chat(input_msg)
            if answer is None:
                answer = "OK"
            try:
                await self.api.post_c2c_message(openid=message.author.user_openid, content=answer, msg_id=message.id)
                print(f"已回复QQ私聊消息：{answer} -> {message.author.user_openid}")
            except Exception as e2:
                print(f"回复QQ私聊消息失败：{e2}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    INTENTS = {"public_messages": True}
    qqbot_client = QBotClient(intents=botpy.Intents(**INTENTS))
    try:
        qqbot_client.run(appid=qq_app_id, secret=qq_app_secret)
    except Exception as e3:
        print(f"QQ机器人运行异常：{e3}")


if dingding_switch == "开启":
    Thread(target=run_dingding).start()
if feishu_switch == "开启":
    Thread(target=run_feishu).start()
if qq_switch == "开启":
    Thread(target=run_qqbot).start()
