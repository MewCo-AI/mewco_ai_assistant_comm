from chat_web import *

app_vrm = Flask(__name__)
vrm_web_template = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="icon" type="image/png" href="/assets/image/logo.png"/>
    <title>VRM 3D角色 - 枫云AI助手社区版</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        body {
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-image: url('/assets/image/bg.jpg');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }
        canvas {
            display: block;
        }
        .touch-indicator {
            position: absolute;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: rgba(255, 215, 0, 0.5);
            pointer-events: none;
            transform: translate(-50%, -50%);
            animation: ripple 0.6s linear;
            z-index: 100;
        }
        @keyframes ripple {
            0% {
                width: 10px;
                height: 10px;
                opacity: 1;
            }
            100% {
                width: 60px;
                height: 60px;
                opacity: 0;
            }
        }
    </style>
</head>
<body>
    <script type="importmap">
        {
            "imports": {
                "three": "/assets/vrm_core/three.module.js",
                "three/addons/": "/assets/vrm_core/jsm/",
                "@pixiv/three-vrm": "/assets/vrm_core/three-vrm.module.min.js"
            }
        }
    </script>
    <script type="module">
        // 从后端获取模型文件名
        const MODEL_FILE_NAME = '{{ model_name }}';  // 使用模板变量
        const MODEL_FILE_PATH = `/assets/vrm_model/${MODEL_FILE_NAME}`;
        import * as THREE from 'three';
        import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
        import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
        import { VRMLoaderPlugin, VRMUtils } from '@pixiv/three-vrm';
        // 初始化场景
        const renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true
        });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        document.body.appendChild(renderer.domElement);
        // 相机
        const camera = new THREE.PerspectiveCamera(30.0, window.innerWidth / window.innerHeight, 0.1, 20.0);
        camera.position.set(0.0, 1.0, 5.0);
        // 相机控制器
        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        controls.screenSpacePanning = true;
        controls.target.set(0.0, 1.0, 0.0);
        controls.update();
        // 场景
        const scene = new THREE.Scene();
        scene.background = null;
        // 灯光
        const light = new THREE.DirectionalLight(0xffffff, Math.PI);
        light.position.set(1.0, 1.0, 1.0).normalize();
        scene.add(light);
        // VRM模型
        let currentVrm = null;
        // 嘴巴动画状态变量
        let isSpeaking = false;
        let mouthOpenTimer = 0;
        let mouthCloseTimer = 0;
        let currentMouthValue = 0;
        const mouthOpenSpeed = 8; // 嘴巴张开速度
        const mouthCloseSpeed = 4; // 嘴巴闭合速度
        const minMouthOpenTime = 0.1; // 最小张开时间
        const maxMouthOpenTime = 0.3; // 最大张开时间
        const minMouthCloseTime = 0.05; // 最小闭合时间
        const maxMouthCloseTime = 0.15; // 最大闭合时间
        // 头部动画变量
        let headXTarget = 0;
        let headYTarget = 0;
        let headZTarget = 0;
        let headMoveTimer = 0;
        const headMoveInterval = 0.5; // 头部动作间隔
        const headMaxAngle = 0.08; // 头部最大旋转角度（弧度）
        // 手臂动画变量
        let leftArmXTarget = 0;
        let leftArmZTarget = 0;
        let rightArmXTarget = 0;
        let rightArmZTarget = 0;
        let armMoveTimer = 0;
        const armMoveInterval = 0.7; // 手臂动作间隔
        const armMaxAngle = 0.1; // 手臂最大旋转角度（弧度）
        // 互动动画状态
        let isInteracting = false;
        let interactionType = null; // 'head', 'leftArm', 'rightArm', 'leftLeg', 'rightLeg'
        let interactionProgress = 0;
        let interactionStep = 0;
        const interactionDuration = 0.5; // 每个互动动作的持续时间（秒）
        // 加载器
        const loader = new GLTFLoader();
        loader.crossOrigin = 'anonymous';
        loader.register((parser) => new VRMLoaderPlugin(parser));
        // 射线检测器
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        function loadVRMModel(url) {
            // 移除先前模型
            if (currentVrm) {
                scene.remove(currentVrm.scene);
                currentVrm = null;
            }
            loader.load(
                url,
                (gltf) => {
                    const vrm = gltf.userData.vrm;
                    // 优化性能
                    VRMUtils.removeUnnecessaryVertices(gltf.scene);
                    VRMUtils.combineSkeletons(gltf.scene);
                    VRMUtils.combineMorphs(vrm);
                    // 禁用视锥体剔除
                    vrm.scene.traverse((obj) => {
                        obj.frustumCulled = false;
                    });
                    scene.add(vrm.scene);
                    currentVrm = vrm;
                    // 设置初始姿势
                    resetToNaturalPose();
                    console.log('VRM模型已加载:', vrm);
                },
                (progress) => console.log('正在加载模型...', (progress.loaded / progress.total * 100).toFixed(2) + '%'),
                (error) => console.error('加载VRM模型时出错:', error)
            );
        }
        // 自然姿势
        function resetToNaturalPose() {
            if (!currentVrm) return;
            // 双手自然下垂
            const leftUpperArm = currentVrm.humanoid.getNormalizedBoneNode('leftUpperArm');
            const leftLowerArm = currentVrm.humanoid.getNormalizedBoneNode('leftLowerArm');
            const rightUpperArm = currentVrm.humanoid.getNormalizedBoneNode('rightUpperArm');
            const rightLowerArm = currentVrm.humanoid.getNormalizedBoneNode('rightLowerArm');
            if (leftUpperArm) leftUpperArm.rotation.set(0, 0, -Math.PI/2.5);
            if (leftLowerArm) leftLowerArm.rotation.set(0, 0, 0);
            if (rightUpperArm) rightUpperArm.rotation.set(0, 0, Math.PI/2.5);
            if (rightLowerArm) rightLowerArm.rotation.set(0, 0, 0);
            // 头部轻微前倾
            const head = currentVrm.humanoid.getNormalizedBoneNode('head');
            if (head) head.rotation.set(0.1, 0, 0);
            // 腿部自然站立
            const leftUpperLeg = currentVrm.humanoid.getNormalizedBoneNode('leftUpperLeg');
            const rightUpperLeg = currentVrm.humanoid.getNormalizedBoneNode('rightUpperLeg');
            if (leftUpperLeg) leftUpperLeg.rotation.set(0, 0, 0);
            if (rightUpperLeg) rightUpperLeg.rotation.set(0, 0, 0);
            // 重置动画目标值
            headXTarget = 0;
            headYTarget = 0;
            headZTarget = 0;
            leftArmXTarget = 0;
            leftArmZTarget = 0;
            rightArmXTarget = 0;
            rightArmZTarget = 0;
        }
        // 更新嘴巴动画
        function updateMouthAnimation(deltaTime) {
            if (!currentVrm || !currentVrm.expressionManager) return;
            if (isSpeaking) {
                // 张开阶段
                if (mouthOpenTimer > 0) {
                    mouthOpenTimer -= deltaTime;
                    currentMouthValue = THREE.MathUtils.lerp(currentMouthValue, 1.0, deltaTime * mouthOpenSpeed);
                } 
                // 闭合阶段
                else if (mouthCloseTimer > 0) {
                    mouthCloseTimer -= deltaTime;
                    currentMouthValue = THREE.MathUtils.lerp(currentMouthValue, 0.0, deltaTime * mouthCloseSpeed);
                }
                // 随机设置下一个动作
                else {
                    if (currentMouthValue > 0.9) {
                        // 从张开到闭合
                        mouthCloseTimer = THREE.MathUtils.randFloat(minMouthCloseTime, maxMouthCloseTime);
                    } else {
                        // 从闭合到张开
                        mouthOpenTimer = THREE.MathUtils.randFloat(minMouthOpenTime, maxMouthOpenTime);
                    }
                }
                // 应用嘴巴表情
                currentVrm.expressionManager.setValue('aa', currentMouthValue * 0.5); // "啊"音口型
                currentVrm.expressionManager.setValue('ih', currentMouthValue * 0.35); // "一"音口型
                currentVrm.expressionManager.setValue('ou', currentMouthValue * 0.25); // "哦"音口型
            } else {
                // 不说话时嘴巴闭合
                currentMouthValue = THREE.MathUtils.lerp(currentMouthValue, 0.0, deltaTime * mouthCloseSpeed);
                currentVrm.expressionManager.setValue('aa', currentMouthValue);
                currentVrm.expressionManager.setValue('ih', currentMouthValue);
                currentVrm.expressionManager.setValue('ou', currentMouthValue);
            }
        }
        // 更新头部动画
        function updateHeadAnimation(deltaTime) {
            if (!currentVrm) return;
            const head = currentVrm.humanoid.getNormalizedBoneNode('head');
            if (!head) return;
            if (isSpeaking) {
                // 计时达到间隔，设置新的头部目标角度
                headMoveTimer += deltaTime;
                if (headMoveTimer >= headMoveInterval) {
                    headMoveTimer = 0;
                    // 随机生成新的目标角度（小幅度）
                    headXTarget = THREE.MathUtils.randFloat(-headMaxAngle, headMaxAngle);
                    headYTarget = THREE.MathUtils.randFloat(-headMaxAngle, headMaxAngle);
                    headZTarget = THREE.MathUtils.randFloat(-headMaxAngle, headMaxAngle);
                }
                // 平滑过渡到目标角度
                head.rotation.x = THREE.MathUtils.lerp(head.rotation.x, 0.1 + headXTarget, deltaTime * 5);
                head.rotation.y = THREE.MathUtils.lerp(head.rotation.y, headYTarget, deltaTime * 5);
                head.rotation.z = THREE.MathUtils.lerp(head.rotation.z, headZTarget, deltaTime * 5);
            } else {
                // 不说话时恢复到自然头部姿势
                head.rotation.x = THREE.MathUtils.lerp(head.rotation.x, 0.1, deltaTime * 3);
                head.rotation.y = THREE.MathUtils.lerp(head.rotation.y, 0, deltaTime * 3);
                head.rotation.z = THREE.MathUtils.lerp(head.rotation.z, 0, deltaTime * 3);
            }
        }
        // 更新手臂动画
        function updateArmAnimation(deltaTime) {
            if (!currentVrm) return;
            const leftUpperArm = currentVrm.humanoid.getNormalizedBoneNode('leftUpperArm');
            const rightUpperArm = currentVrm.humanoid.getNormalizedBoneNode('rightUpperArm');
            if (!leftUpperArm || !rightUpperArm) return;
            if (isSpeaking) {
                // 计时达到间隔，设置新的手臂目标角度
                armMoveTimer += deltaTime;
                if (armMoveTimer >= armMoveInterval) {
                    armMoveTimer = 0;
                    // 随机生成新的目标角度（小幅度）
                    leftArmXTarget = THREE.MathUtils.randFloat(-armMaxAngle, armMaxAngle);
                    leftArmZTarget = THREE.MathUtils.randFloat(-armMaxAngle, armMaxAngle);
                    rightArmXTarget = THREE.MathUtils.randFloat(-armMaxAngle, armMaxAngle);
                    rightArmZTarget = THREE.MathUtils.randFloat(-armMaxAngle, armMaxAngle);
                }
                // 平滑过渡到目标角度（基于自然姿势）
                leftUpperArm.rotation.x = THREE.MathUtils.lerp(
                    leftUpperArm.rotation.x, 
                    0 + leftArmXTarget, 
                    deltaTime * 5
                );
                leftUpperArm.rotation.z = THREE.MathUtils.lerp(
                    leftUpperArm.rotation.z, 
                    -Math.PI/2.5 + leftArmZTarget, 
                    deltaTime * 5
                );
                rightUpperArm.rotation.x = THREE.MathUtils.lerp(
                    rightUpperArm.rotation.x, 
                    0 + rightArmXTarget, 
                    deltaTime * 5
                );
                rightUpperArm.rotation.z = THREE.MathUtils.lerp(
                    rightUpperArm.rotation.z, 
                    Math.PI/2.5 + rightArmZTarget, 
                    deltaTime * 5
                );
            } else {
                // 不说话时恢复到自然手臂姿势
                leftUpperArm.rotation.x = THREE.MathUtils.lerp(leftUpperArm.rotation.x, 0, deltaTime * 3);
                leftUpperArm.rotation.z = THREE.MathUtils.lerp(leftUpperArm.rotation.z, -Math.PI/2.5, deltaTime * 3);
                rightUpperArm.rotation.x = THREE.MathUtils.lerp(rightUpperArm.rotation.x, 0, deltaTime * 3);
                rightUpperArm.rotation.z = THREE.MathUtils.lerp(rightUpperArm.rotation.z, Math.PI/2.5, deltaTime * 3);
            }
        }
        // 检查音频播放状态
        async function checkAudioPlaying() {
            try {
                const response = await fetch('/is_audio_playing');
                const data = await response.json();
                isSpeaking = data.is_playing;
            } catch (error) {
                console.error('检测音频播放状态失败:', error);
            }
        }
        // 加载默认模型
        loadVRMModel(MODEL_FILE_PATH);
        // 动画参数
        let blinkTimer = 0;
        const blinkDuration = 0.2; // 眨眼持续时间
        let isBlinking = false;
        let breathTimer = 0;
        const breathCycle = 4; // 呼吸周期（秒）
        // 动画循环
        const clock = new THREE.Clock();
        function animate() {
            requestAnimationFrame(animate);
            const deltaTime = clock.getDelta();
            if (currentVrm) {
                // 更新呼吸动画
                updateBreathAnimation(deltaTime);
                // 更新眨眼动画
                updateBlinkAnimation(deltaTime);
                // 更新嘴巴动画
                updateMouthAnimation(deltaTime);
                // 更新头部动画
                updateHeadAnimation(deltaTime);
                // 更新手臂动画
                updateArmAnimation(deltaTime);
                // 更新互动动画
                updateInteractionAnimation(deltaTime);
                // 更新VRM
                currentVrm.update(deltaTime);
            }
            // 更新控制器阻尼
            controls.update();
            // 渲染场景
            renderer.render(scene, camera);
        }
        // 呼吸动画
        function updateBreathAnimation(deltaTime) {
            breathTimer += deltaTime;
            const breathProgress = (breathTimer % breathCycle) / breathCycle;
            const breathValue = Math.sin(breathProgress * Math.PI * 2);
            // 应用到胸部（脊柱）
            const spine = currentVrm.humanoid.getNormalizedBoneNode('spine');
            if (spine) {
                spine.position.y = 0.9 * breathValue;
                spine.rotation.x = 1.5 * Math.sin(breathProgress * Math.PI * 2 + Math.PI/2) * THREE.MathUtils.DEG2RAD;
            }
            // 肩膀轻微起伏
            const leftShoulder = currentVrm.humanoid.getNormalizedBoneNode('leftShoulder');
            const rightShoulder = currentVrm.humanoid.getNormalizedBoneNode('rightShoulder');
            if (leftShoulder) leftShoulder.rotation.z = 0.5 * breathValue * THREE.MathUtils.DEG2RAD;
            if (rightShoulder) rightShoulder.rotation.z = -0.5 * breathValue * THREE.MathUtils.DEG2RAD;
        }
        // 眨眼动画
        function updateBlinkAnimation(deltaTime) {
            blinkTimer += deltaTime;
            if (blinkTimer >= 2 && !isBlinking) {
                isBlinking = true;
                blinkTimer = 0;
            }
            if (isBlinking) {
                const blinkProgress = Math.min(blinkTimer / blinkDuration, 1);
                const blinkValue = Math.pow(blinkProgress, 0.5);
                if (currentVrm.expressionManager) {
                    currentVrm.expressionManager.setValue('blink', blinkValue);
                    currentVrm.expressionManager.setValue('blinkLeft', blinkValue);
                    currentVrm.expressionManager.setValue('blinkRight', blinkValue);
                }
                if (blinkProgress >= 1) {
                    isBlinking = false;
                    blinkTimer = 0;
                    if (currentVrm.expressionManager) {
                        currentVrm.expressionManager.setValue('blink', 1);
                        currentVrm.expressionManager.setValue('blinkLeft', 1);
                        currentVrm.expressionManager.setValue('blinkRight', 1);
                    }
                    setTimeout(() => {
                        if (currentVrm.expressionManager) {
                            currentVrm.expressionManager.setValue('blink', 0);
                            currentVrm.expressionManager.setValue('blinkLeft', 0);
                            currentVrm.expressionManager.setValue('blinkRight', 0);
                        }
                    }, 100);
                } else {
                    blinkTimer += deltaTime;
                }
            }
        }
        // 更新互动动画
        function updateInteractionAnimation(deltaTime) {
            if (!isInteracting || !currentVrm) return;
            interactionProgress += deltaTime;
            // 计算当前动作进度 (0-1)
            let progress = Math.min(interactionProgress / interactionDuration, 1);
            // 获取相关骨骼
            const head = currentVrm.humanoid.getNormalizedBoneNode('head');
            const leftUpperArm = currentVrm.humanoid.getNormalizedBoneNode('leftUpperArm');
            const rightUpperArm = currentVrm.humanoid.getNormalizedBoneNode('rightUpperArm');
            const leftUpperLeg = currentVrm.humanoid.getNormalizedBoneNode('leftUpperLeg');
            const rightUpperLeg = currentVrm.humanoid.getNormalizedBoneNode('rightUpperLeg');
            // 应用动画效果
            switch(interactionType) {
                case 'head':
                    if (head) {
                        // 点头动画 (上下移动)
                        const nodAmount = Math.sin(progress * Math.PI * 2) * 0.2;
                        head.rotation.x = 0.1 + nodAmount;
                    }
                    break;
                case 'leftArm':
                    if (leftUpperArm) {
                        // 手臂摆动动画
                        const swingAmount = Math.sin(progress * Math.PI * 2) * 0.5;
                        leftUpperArm.rotation.z = -Math.PI/2.5 + swingAmount;
                    }
                    break;
                case 'rightArm':
                    if (rightUpperArm) {
                        // 手臂摆动动画
                        const swingAmount = Math.sin(progress * Math.PI * 2) * 0.5;
                        rightUpperArm.rotation.z = Math.PI/2.5 - swingAmount;
                    }
                    break;
                case 'leftLeg':
                    if (leftUpperLeg) {
                        // 腿部摆动动画
                        const liftAmount = Math.sin(progress * Math.PI * 2) * 0.3;
                        leftUpperLeg.rotation.x = -liftAmount;
                    }
                    break;
                case 'rightLeg':
                    if (rightUpperLeg) {
                        // 腿部摆动动画
                        const liftAmount = Math.sin(progress * Math.PI * 2) * 0.3;
                        rightUpperLeg.rotation.x = -liftAmount;
                    }
                    break;
            }
            // 检查是否完成一个动作周期
            if (progress >= 1) {
                interactionStep++;
                interactionProgress = 0;
                // 完成两次动作后结束互动
                if (interactionStep >= 2) {
                    isInteracting = false;
                    interactionType = null;
                    interactionStep = 0;
                    // 恢复自然姿势
                    resetToNaturalPose();
                }
            }
        }
        // 处理触摸/点击事件
        function onTouch(event) {
            if (!currentVrm) return;
            // 计算鼠标位置
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
            // 设置射线
            raycaster.setFromCamera(mouse, camera);
            // 检测与模型相交
            const intersects = raycaster.intersectObjects(currentVrm.scene.children, true);
            if (intersects.length > 0) {
                const point = intersects[0].point;
                // 获取骨骼位置
                const headPos = getBonePosition('head');
                const leftArmPos = getBonePosition('leftUpperArm');
                const rightArmPos = getBonePosition('rightUpperArm');
                const leftLegPos = getBonePosition('leftUpperLeg');
                const rightLegPos = getBonePosition('rightUpperLeg');
                // 计算距离
                const headDist = headPos ? point.distanceTo(headPos) : Infinity;
                const leftArmDist = leftArmPos ? point.distanceTo(leftArmPos) : Infinity;
                const rightArmDist = rightArmPos ? point.distanceTo(rightArmPos) : Infinity;
                const leftLegDist = leftLegPos ? point.distanceTo(leftLegPos) : Infinity;
                const rightLegDist = rightLegPos ? point.distanceTo(rightLegPos) : Infinity;
                // 找出最近的骨骼
                const minDist = Math.min(headDist, leftArmDist, rightArmDist, leftLegDist, rightLegDist);
                if (minDist > 0.2) return; // 太远则不响应
                // 触发相应互动
                if (!isInteracting) {
                    if (minDist === headDist) {
                        startInteraction('head');
                    } else if (minDist === leftArmDist) {
                        startInteraction('leftArm');
                    } else if (minDist === rightArmDist) {
                        startInteraction('rightArm');
                    } else if (minDist === leftLegDist) {
                        startInteraction('leftLeg');
                    } else if (minDist === rightLegDist) {
                        startInteraction('rightLeg');
                    }
                }
            }
        }
        // 获取骨骼位置
        function getBonePosition(boneName) {
            if (!currentVrm) return null;
            const bone = currentVrm.humanoid.getNormalizedBoneNode(boneName);
            if (!bone) return null;
            const worldPos = new THREE.Vector3();
            bone.getWorldPosition(worldPos);
            return worldPos;
        }
        // 开始互动动画
        function startInteraction(type) {
            isInteracting = true;
            interactionType = type;
            interactionProgress = 0;
            interactionStep = 0;
            console.log(`开始互动: ${type}`);
        }
        animate();
        // 定时检查音频播放状态（每200ms）
        setInterval(checkAudioPlaying, 200);
        // 窗口大小调整
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        // 添加触摸/点击事件监听
        window.addEventListener('mousedown', onTouch);
        window.addEventListener('touchstart', (event) => {
            if (event.touches.length > 0) {
                onTouch(event.touches[0]);
            }
        }, { passive: true });
    </script>
</body>
</html>
'''


@app_vrm.route('/')
def index():
    return render_template_string(vrm_web_template, model_name=vrm_model_name)


@app_vrm.route('/assets/vrm_model/<path:filename>')
def serve_vrm_model(filename):
    return send_from_directory('dist/assets/vrm_model', filename)


@app_vrm.route('/assets/vrm_core/<path:filename>')
def serve_vrm_core(filename):
    return send_from_directory('dist/assets/vrm_core', filename)


@app_vrm.route('/assets/image/<path:filename>')
def serve_image(filename):
    return send_from_directory('dist/assets/image', filename)


@app_vrm.route('/is_audio_playing')
def is_audio_playing():
    try:
        is_playing = pg.mixer.music.get_busy() if pg.mixer.get_init() else False
        return jsonify({'is_playing': is_playing})
    except:
        return jsonify({'is_playing': False})


def run_vrm():
    app_vrm.run(port=vrm_port, host="0.0.0.0")
