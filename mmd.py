import json
import logging
import random
import pygame as pg
from flask import Flask, send_from_directory, render_template_string

with open('data/db/config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)
mmd_port = int(config["MMD角色网页端口"])
app = Flask(__name__, static_folder='dist')
logging.getLogger('werkzeug').setLevel(logging.ERROR)

mmd_web_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="icon" type="image/png" href="assets/image/logo.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MMD 3D角色 - 枫云AI助手社区版</title>
    <style>
        body {
            margin: 0;
            background-image: url('/assets/image/bg.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        canvas {
            display: block;
        }
    </style>
</head>
<body>
    <script src="/assets/mmd_core/ammo.js"></script>
    <script src="/assets/mmd_core/mmdparser.min.js"></script>
    <script src="/assets/mmd_core/three.min.js"></script>
    <script src="/assets/mmd_core/CCDIKSolver.js"></script>
    <script src="/assets/mmd_core/MMDPhysics.js"></script>
    <script src="/assets/mmd_core/TGALoader.js"></script>
    <script src="/assets/mmd_core/MMDLoader.js"></script>
    <script src="/assets/mmd_core/OrbitControls.js"></script>
    <script src="/assets/mmd_core/MMDAnimationHelper.js"></script>
    <script src="/assets/mmd.js"></script>
</body>
</html>
"""

mmd_vmd_web_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="icon" type="image/png" href="assets/image/logo.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MMD 3D动作 - 枫云AI助手社区版</title>
    <style>
        body {
            margin: 0;
            background-image: url('/assets/image/bg.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        canvas { display: block; }
    </style>
</head>
<body>
    <script src="/assets/mmd_core/ammo.js"></script>
    <script src="/assets/mmd_core/mmdparser.min.js"></script>
    <script src="/assets/mmd_core/three.min.js"></script>
    <script src="/assets/mmd_core/CCDIKSolver.js"></script>
    <script src="/assets/mmd_core/MMDPhysics.js"></script>
    <script src="/assets/mmd_core/TGALoader.js"></script>
    <script src="/assets/mmd_core/MMDLoader.js"></script>
    <script src="/assets/mmd_core/OrbitControls.js"></script>
    <script src="/assets/mmd_core/MMDAnimationHelper.js"></script>
    <script src="/assets/mmd_vmd.js"></script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(mmd_web_template)


@app.route('/vmd')
def index_vmd():
    return render_template_string(mmd_vmd_web_template)


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


def run_mmd():
    app.run(port=mmd_port, host="0.0.0.0")
