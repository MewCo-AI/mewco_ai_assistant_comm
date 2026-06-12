import json
import logging
import random
import pygame as pg
from flask import Flask, send_from_directory, render_template_string

with open('data/db/config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)
live2d_port = int(config["L2D角色网页端口"])
app = Flask(__name__, static_folder='dist')
logging.getLogger('werkzeug').setLevel(logging.ERROR)

live2d_web_template = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/png" href="assets/image/logo.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <style>
      body {
        background-image: url('assets/image/bg.jpg');
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center center;
        background-attachment: fixed;
      }
      #canvas2 {
        width: 60%;
        height: auto;
        margin: 50px auto;
        display: block;
        background-color: transparent;
      }
    </style>
    <script src="/assets/live2d_core/live2dcubismcore.min.js"></script>
    <script src="/assets/live2d_core/live2d.min.js"></script>
    <script src="/assets/live2d_core/pixi.min.js"></script>
    <title>Live2D角色 - 枫云AI助手社区版</title>
    <script type="module" crossorigin src="/assets/live2d.js"></script>
  </head>
  <body>
    <div id="app"></div>
    <canvas id="canvas2"></canvas>
  </body>
</html>
"""

live2d_pet_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/png" href="assets/image/logo.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <style>
        html, body {
            margin: 0; /* 去掉默认边距 */
            padding: 0; /* 去掉默认内边距 */
            overflow: hidden; /* 禁用溢出滚动条 */
            width: 100%; /* 100%宽度 */
            height: 100%; /* 100%高度 */
        }
        #canvas2 {
            width: 800px; /* 指定固定宽度 */
            height: 600px; /* 指定固定高度 */
            display: block;
            background-color: transparent;
        }
    </style>
    <script src="/assets/live2d_core/live2dcubismcore.min.js"></script>
    <script src="/assets/live2d_core/live2d.min.js"></script>
    <script src="/assets/live2d_core/pixi.min.js"></script>
    <title>桌宠 - 枫云AI助手社区版</title>
    <script type="module" crossorigin src="/assets/live2d.js"></script>
    <script>
        // 在页面加载完成后设置滚动位置
        window.onload = function () {
            // 设置向右滑动的距离，这里设置为225px，你可以根据需要调整
            document.body.scrollLeft = 225;
        };
    </script>
</head>
<body>
    <div id="app"></div>
    <canvas id="canvas2"></canvas>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(live2d_web_template)


@app.route('/pet')
def desktop_pet():
    return render_template_string(live2d_pet_template)


@app.route('/assets/<path:path>')
def serve_static(path):
    if path.endswith(".js"):
        return send_from_directory('./dist/assets', path, mimetype='application/javascript')
    return send_from_directory('./dist/assets', path)


@app.route('/api/get_mouth_y')
def check_play_state():
    is_playing = pg.mixer.music.get_busy() if pg.mixer.get_init() else False
    if is_playing:
        return json.dumps({"y": random.uniform(0.1, 0.9)})
    else:
        return json.dumps({"y": 0})


def run_live2d():
    app.run(port=live2d_port, host="0.0.0.0")
