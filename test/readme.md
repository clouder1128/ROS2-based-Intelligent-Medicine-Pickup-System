## 文件夹内容

world/test_world.sdf中创建了一个简易的世界，用于模拟小车的巡线功能。

models/中包含了带摄像头的轮式差速小车模型、场地模型（忽略另外两个模型）。

models/new_car:小车模型在/cmd_vel话题下接受速度消息并移动，可以通过teleop发布消息进行控制。相机可以在/camera话题发布消息，传送画面可以在image display中查看。

## TODO 

- 希望实现通过python程序控制小车自动巡线。
- 希望实现小车可以在指定位置停下（红点可以作为提示），直到接收到一个消息（目前未定义）后继续巡线移动。
- 希望上述过程可以在整个巡线过程中发生多次。

参考教程：https://www.bilibili.com/video/BV1RjS2YHE7Z?spm_id_from=333.788.videopod.sections&vd_source=70ad62eeba83c73634a3120fe532319b
