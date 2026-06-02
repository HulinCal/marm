# Marm - 简单机械臂仿真项目

这是一个基于 ROS 2 和 Gazebo 的简单机械臂仿真项目，支持使用 MoveIt 进行运动规划和控制。
                                仿真显示
![仿真显示]

(https://github.com/HulinCal/marm/blob/main/src/11-2026-06-02_12.56.40.mp4)


## 项目结构

```
marm_ws/
├── src/
│   ├── marm/                    # 主包 - 机器人描述和启动文件
│   │   ├── config/              # 控制器配置
│   │   ├── launch/              # 启动文件
│   │   └── urdf/                # URDF 机器人模型
│   ├── marm_control_pkg/        # C++ 控制包
│   │   └── src/
│   │       ├── arm_control_cpp_node.cpp      # 关节角度控制节点
│   │       └── pose_control_cpp_node.cpp     # 位姿控制节点（含夹爪）
│   ├── marm_control_pkg_py/     # Python 控制包
│   └── marm_moveit_config/      # MoveIt 配置包
├── build/                       # 构建目录
└── install/                     # 安装目录
```

## 功能特性

- 🤖 **机械臂仿真**: 使用 Gazebo 进行机械臂动力学仿真
- 📐 **运动规划**: 使用 MoveIt 进行逆运动学求解和路径规划
- 🔧 **关节控制**: 支持通过关节角度控制机械臂运动
- 🎯 **位姿控制**: 支持通过末端位姿控制机械臂运动
- 🦾 **夹爪控制**: 支持夹爪的开合控制

## 环境要求

- ROS 2 jazzy 或更高版本
- Gazebo Garden 或更高版本
- MoveIt 2
- ros_gz 桥接包

## 安装与构建

```bash
# 进入工作空间
cd ~/marm_ws

# 构建项目
colcon build --symlink-install

# 激活环境
source install/setup.bash
```

## 快速开始

### 启动完整仿真环境

```bash
ros2 launch marm gazebo_moveit_bringup.launch.py
```

该命令会启动：
- Gazebo 仿真环境
- Robot State Publisher
- ROS-Gazebo 桥接
- 关节控制器（arm_controller, gripper_controller）
- MoveGroup 运动规划节点
- RViz 可视化界面

### 运行关节控制节点

```bash
ros2 run marm_control_pkg arm_control_cpp_node
```

该节点会将机械臂移动到指定的关节角度位置。

### 运行位姿控制节点

```bash
ros2 run marm_control_pkg pose_control_cpp_node
```

该节点会：
1. 机械臂回到 HOME 位置
2. 移动到目标位姿
3. 闭合夹爪
4. 打开夹爪

## 核心文件说明

### 启动文件

- `launch/gazebo_moveit_bringup.launch.py` - 完整仿真环境启动文件

### 控制节点

| 文件 | 功能 | 语言 |
|------|------|------|
| `arm_control_cpp_node.cpp` | 关节角度控制 | C++ |
| `pose_control_cpp_node.cpp` | 位姿控制 + 夹爪控制 | C++ |
| `pose_control_py_node.py` | 位姿控制（Python版） | Python |

### 机器人描述

- `urdf/arm.urdf` - 机器人 URDF 描述文件
- `urdf/arm.urdf.xacro` - XACRO 宏定义文件

## 控制器配置

控制器配置位于 `config/marm_ros2_controllers.yaml`，包含：
- `joint_state_broadcaster` - 关节状态广播器
- `arm_controller` - 机械臂关节控制器
- `gripper_controller` - 夹爪控制器

## 使用示例

### 在 RViz 中手动控制

1. 启动仿真环境
2. 在 RViz 中使用 MotionPlanning 插件
3. 拖动末端执行器到目标位置
4. 点击 "Plan" 按钮规划路径
5. 点击 "Execute" 按钮执行运动

### 通过代码控制

参考 `src/marm_control_pkg/src/` 目录下的示例代码，实现自定义的运动控制逻辑。

## 许可证

此项目采用 Apache-2.0 许可证，详见 LICENSE 文件。

## 维护者

- hl <3352885695@qq.com>
