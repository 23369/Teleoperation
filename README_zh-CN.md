<div align="center">
  <h1 align="center"> avp_teleoperate </h1>
  <h3 align="center"> Unitree Robotics </h3>
  <p align="center">
    <a href="README.md"> English </a> | <a>中文</a>
  </p>
</div>

# 📺 视频演示

<p align="center">
  <a href="https://www.bilibili.com/video/BV1SW421X7kA">
    <img src="./img/video_cover.jpg" alt="Watch the video" style="width: 35%;">
  </a>
</p>

# 0. 📖 介绍

该仓库实现了使用 **Apple Vision Pro** 对 **宇树（Unitree）人形机器人** 的遥操作控制。

以下是本仓库将支持的机器人类型：

<table>
  <tr>
    <th style="text-align: center;"> &#129302; 机器人 </th>
    <th style="text-align: center;"> &#9898; 状态 </th>
  </tr>
  <tr>
    <td style="text-align: center;"> G1 (29自由度) + Dex3-1 </td>
    <td style="text-align: center;"> &#9989; 完成 </td>
  </tr>
  <tr>
    <td style="text-align: center;"> G1 (23自由度) </td>
    <td style="text-align: center;"> &#9201; 进行中 </td>
  </tr>
  <tr>
    <td style="text-align: center;"> H1 (手臂4自由度) </td>
    <td style="text-align: center;"> &#9201; 进行中 </td>
  </tr>
  <tr>
    <td style="text-align: center;"> H1_2 (手臂7自由度) + Inspire </td>
    <td style="text-align: center;"> &#9201; 进行中 </td>
  </tr>
  <tr>
    <td style="text-align: center;"> ··· </td>
    <td style="text-align: center;"> ··· </td>
  </tr>
</table>



# 1. 📦 前置条件

我们在 Ubuntu 20.04 和 Ubuntu 22.04 上测试了我们的代码，其他操作系统可能需要不同的配置。

有关更多信息，您可以参考 [官方文档](https://support.unitree.com/home/zh/Teleoperation) 和 [OpenTeleVision](https://github.com/OpenTeleVision/TeleVision)。

## 1.1 🦾 逆运动学

```bash
conda create -n tv python=3.8
conda activate tv
# 如果您使用 `pip install`，请确保 pinocchio 版本为 3.1.0
conda install pinocchio -c conda-forge
pip install meshcat
pip install casadi
```

## 1.2 🕹️ unitree_dds_wrapper

```bash
# 安装 unitree_dds_wrapper 的 Python 版本
git clone https://github.com/unitreerobotics/unitree_dds_wrapper.git
cd unitree_dds_wrapper/python
pip install -e .
```

> 注意：这是一个临时版本，未来将被 [unitree_sdk2_python](https://github.com/unitreerobotics/unitree_sdk2_python) 取代。



# 2. 🛠️ TeleVision 和 Apple Vision Pro 配置

## 2.1 📥 基础

```bash
cd ~
git clone https://github.com/unitreerobotics/avp_teleoperate.git 
cd ~/avp_teleoperate
pip install -r requirements.txt
cd act/detr && pip install -e .
```

## 2.2 🔌 本地流媒体

**Apple** 不允许在非 HTTPS 连接上使用 WebXR。要在本地测试应用程序，我们需要创建一个自签名证书并在客户端上安装它。您需要一台 Ubuntu 机器和一个路由器。将 Apple Vision Pro 和 Ubuntu **主机**连接到同一个路由器。

1. 安装 mkcert：https://github.com/FiloSottile/mkcert
2. 检查**主机**本地 IP 地址：

```bash
ifconfig | grep inet
```

假设 **主机** 的本地 IP 地址为 `192.168.123.2`

> 注意：您可以使用 `ifconfig` 命令检查您的 **主机** IP 地址。

3. 创建证书：

```bash
mkcert -install && mkcert -cert-file cert.pem -key-file key.pem 192.168.123.2 localhost 127.0.0.1
```

将生成的 `cert.pem` 和 `key.pem` 文件放在 `teleop` 目录中

```bash
cp cert.pem key.pem ~/avp_teleoperate/teleop/
```

4. 在服务器上打开防火墙：

```bash
sudo ufw allow 8012
```

5. 在 Apple Vision Pro 上安装 CA 证书：

```bash
mkcert -CAROOT
```

通过 AirDrop 将 `rootCA.pem` 复制到 Apple Vision Pro 并安装它。

设置 > 通用 > 关于本机 > 证书信任设置。在“启用对根证书的完全信任”下，打开对证书的信任。

设置 > 应用 > Safari > 高级 > 功能标志 > 启用 WebXR 相关功能。

## 2.3 🔎 测试环境

此步骤用于验证环境是否正确安装。

1. 下载 Isaac Gym：https://developer.nvidia.com/isaac-gym/download

   解压到当前目录，进入 `IsaacGym_Preview_4_Package/isaacgym/python` 目录，执行命令：

   ```bash
   pip install -e .
   ```

2. 按照上述说明设置本地流媒体后，您可以尝试在 Isaac Gym 中远程操作两个机器人手：

   ```bash
   cd teleop
   python teleop_test_gym.py
   ```

3. 戴上您的 Apple Vision Pro 设备。

4. 在 Apple Vision Pro 上打开 Safari，访问：https://192.168.123.2:8012?ws=wss://192.168.123.2:8012

   > 注意：此 IP 地址应与您的 **主机** IP 地址匹配。

5. 点击 `Enter VR` 并选择 `Allow` 以启动 VR 会话。

6. 在 3D 中看到您的手！

<div style="center">
  <img src="https://oss-global-cdn.unitree.com/static/d079e884c3074e8495f81e78c9586f7f_2556x1179.jpg" width="50%">
</div>


# 3. 🚀 使用方法

在开始此程序之前，请至少阅读一次 [官方文档](https://support.unitree.com/home/zh/Teleoperation)。

## 3.1 🖼️ 图像服务器

将 `avp_teleoperate/teleop/image_server` 目录中的 `image_server.py` 复制到宇树机器人（G1/H1/H1_2 等）的 **开发计算单元 PC2**，并在 **PC2** 上执行以下命令：

```bash
# 提醒1：可以通过scp命令将image_server.py传输到PC2，然后使用ssh远程登录PC2后执行它。
# 提醒2：目前该图像传输程序是为双目RGB相机配置的。

# 现在位于宇树机器人 PC2 终端
python image_server.py
# 您可以看到终端输出如下：
# 图像服务器已启动，等待客户端连接...
# 图像分辨率：宽度为 x，高度为 x
```

在图像服务启动后，您可以在 **主机** 终端上使用 `image_client.py` 测试通信是否成功：

```bash
python image_client.py
```

## 3.2 ✋ Inspire 手部服务器（可选）

您可以参考 [灵巧手开发](https://support.unitree.com/home/zh/H1_developer/Dexterous_hand) 配置相关环境并编译控制程序。首先，使用 [此链接](https://oss-global-cdn.unitree.com/static/0a8335f7498548d28412c31ea047d4be.zip) 下载灵巧手控制接口程序，然后将其复制到宇树机器人的**PC2**。

在宇树机器人的 **PC2** 上，执行命令：

```bash
sudo apt install libboost-all-dev libspdlog-dev
# 构建项目
cd h1_inspire_service && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make
# 终端 1. 运行 h1 inspire 手部服务
sudo ./inspire_hand -s /dev/ttyUSB0
# 终端 2. 运行示例
./h1_hand_example
```

如果两只手连续打开和关闭，则表示成功。一旦成功，关闭终端 2 中的 `./h1_hand_example` 程序。

## 3.3 🚀 启动

>  ![Warning](https://img.shields.io/badge/Warning-Important-red)
>
> 1. 所有人员必须与机器人保持安全距离，以防止任何潜在的危险！
> 2. 在运行此程序之前，请确保至少阅读一次 [官方文档](https://support.unitree.com/home/zh/Teleoperation)。

最好有两名操作员来运行此程序，称为 **操作员 A** 和 **操作员 B**。

现在，**操作员 B** 在 **主机** 上执行以下命令：

```bash
python teleop_hand_and_arm.py
```

然后，**操作员 A**：

1. 戴上您的 Apple Vision Pro 设备。

2. 在 Apple Vision Pro 上打开 Safari，访问：https://192.168.123.2:8012?ws=wss://192.168.123.2:8012

   > 注意：此 IP 地址应与您的 **主机** IP 地址匹配。

3. 点击 `Enter VR` 并选择 `Allow` 以启动 VR 会话。

当主机终端输出“Please enter the start signal (enter 'r' to start the subsequent program):”时，**操作员 B** 可以在终端中按下 **r** 键以启动远程操作程序。

此时，**操作员 A** 可以远程控制机器人的手臂和灵巧手。

接下来，**操作员 B** 可以在打开的“record image”窗口中按 **s** 键开始录制数据，再次按 **s** 键停止。可以根据需要重复此操作进行多次录制。

> 注意：录制的数据默认存储在 `avp_teleoperate/teleop/data` 中，使用说明见此仓库： [unitree_IL_lerobot](https://github.com/unitreerobotics/unitree_IL_lerobot/blob/main/README_zh.md#%E6%95%B0%E6%8D%AE%E9%87%87%E9%9B%86%E4%B8%8E%E8%BD%AC%E6%8D%A2)。

## 3.4 🔚 退出

>  ![Warning](https://img.shields.io/badge/Warning-Important-red)
>
> 为了避免损坏机器人，最好确保**操作员 A** 将机器人手臂摆放为自然下垂或其他恰当位置后，**操作员B **再按 **q** 退出。

要退出程序，**操作员 B** 可以在“record image”窗口中按下 **q** 键。



# 4. 🗺️ 代码库教程

```
avp_teleoperate/
│
├── assets                    [存储机器人 URDF 相关文件]
│
├── teleop
│   ├── image_server
│   │     ├── image_client.py      [用于从机器人图像服务器接收图像数据]
│   │     ├── image_server.py      [从摄像头捕获图像并通过网络发送（在机器人板载计算单元上运行）]
│   │
│   ├── open_television
│   │      ├── television.py       [使用 Vuer 从 Apple Vision Pro 捕获腕部和手部数据]  
│   │      ├── tv_wrapper.py       [对捕获的数据进行后处理]
│   │
│   ├── robot_control
│   │      ├── robot_arm_ik.py     [手臂的逆运动学]  
│   │      ├── robot_arm.py        [控制双臂关节并锁定其他部分]
│   │      ├── robot_hand_inspire.py  [控制因时灵巧手]
│   │      ├── robot_hand_unitree.py  [控制宇树灵巧手]
│   │
│   ├── utils
│   │      ├── episode_writer.py          [用于记录模仿学习的数据]  
│   │      ├── mat_tool.py                [一些小的数学工具]
│   │      ├── weighted_moving_filter.py  [用于过滤关节数据的滤波器]
│   │
│   │──teleop_hand_and_arm.py    [遥操作的启动执行代码]
|   |——teleop_test_gym.py        [可用于验证环境是否正确安装]
```



# 5. 🙏 鸣谢

该代码基于以下开源代码库构建。请访问以下链接查看各自的许可证：

1. https://github.com/OpenTeleVision/TeleVision
2. https://github.com/dexsuite/dex-retargeting
3. https://github.com/vuer-ai/vuer
4. https://github.com/stack-of-tasks/pinocchio
5. https://github.com/casadi/casadi
6. https://github.com/meshcat-dev/meshcat-python
7. https://github.com/zeromq/pyzmq
8. https://github.com/unitreerobotics/unitree_dds_wrapper
9. https://github.com/tonyzhaozh/act
10. https://github.com/facebookresearch/detr
11. https://github.com/Dingry/BunnyVisionPro