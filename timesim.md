# MoveGroup 未使用 sim_time 问题的解决方案

## 问题描述

MoveGroup 节点启动时默认使用系统时间（`use_sim_time: false`），而 Gazebo 仿真环境使用仿真时间（`/clock` 话题）。这导致：

- MoveIt 请求的时间戳（系统时间）与实际关节状态时间戳（仿真时间）不匹配
- 轨迹执行验证失败，提示 "Didn't receive robot state with recent timestamp"
- TF 缓冲区检测到时间回跳，提示 "Detected jump back in time. Clearing TF buffer."
- 轨迹执行状态显示 PREEMPTED，执行失败

## 问题诊断

### 步骤 1：检查 MoveGroup 的 use_sim_time 参数

```bash
ros2 param get /move_group use_sim_time
```

**预期结果**：`Boolean value is: False`（确认问题存在）

### 步骤 2：检查时钟话题时间戳

```bash
ros2 topic echo /clock --once
ros2 topic echo /joint_states --once
```

**预期结果**：两个话题的时间戳差异巨大（数百甚至数千秒），说明时钟未同步

### 步骤 3：检查控制器状态

```bash
ros2 control list_controllers
```

**预期结果**：控制器已激活但无法执行轨迹

## 解决方案

### 修改 move_group.launch.py

**文件路径**：`/home/hl/marm_ws/src/marm_moveit_config/launch/move_group.launch.py`

**问题根源**：`generate_move_group_launch()` 函数不会自动将 `use_sim_time` 参数传递给 MoveGroup 节点

**修改后的代码**：

```python
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    moveit_config = MoveItConfigsBuilder("marm", package_name="marm_moveit_config") \
        .trajectory_execution().to_moveit_configs()

    ld = generate_move_group_launch(moveit_config)

    # 添加 use_sim_time 参数声明
    ld.add_action(DeclareLaunchArgument('use_sim_time', default_value='true'))

    # 延迟 3 秒执行 ros2 param set，确保节点已完全启动
    set_param_cmd = ExecuteProcess(
        cmd=['bash', '-c', 'sleep 3 && ros2 param set /move_group use_sim_time true'],
        output='screen'
    )
    ld.add_action(TimerAction(period=1.0, actions=[set_param_cmd]))

    return ld
```

**关键点说明**：

1. 声明 `use_sim_time` LaunchArgument，默认为 `true`
2. 使用 `ExecuteProcess` 执行 `ros2 param set /move_group use_sim_time true` 命令
3. 使用 `TimerAction` 延迟 1 秒后执行，确保 MoveGroup 节点已完全启动

### 修改 gazebo_moveit_bringup.launch.py

**文件路径**：`/home/hl/marm_ws/src/marm/launch/gazebo_moveit_bringup.launch.py`

**关键改进**：

1. 重新组织启动顺序，确保时钟桥接在 MoveIt 之前启动
2. 延迟启动 MoveIt，确保时钟桥接已正常运行
3. 添加独立的 robot_state_publisher，明确设置 `use_sim_time: true`
4. 添加关节状态桥接节点，正确桥接 Gazebo 的关节状态

**修改后的启动顺序**：

```python
return LaunchDescription([
    DeclareLaunchArgument("use_sim_time", default_value="true"),

    # 第一阶段：Gazebo 和基础设置
    gazebo,
    rsp,
    spawn_entity,

    # 第二阶段：状态发布和时钟桥接
    robot_state_publisher,
    clock_bridge,
    joint_states_bridge,

    # 第三阶段：控制器
    spawn_jsb,
    spawn_arm,
    spawn_gripper,

    # 第四阶段：MoveIt 和 RViz（延迟启动）
    move_group,  # TimerAction(period=3.0)
    rviz,
])
```

**关键代码片段**：

```python
# 时钟桥接 - 在 MoveIt 之前启动
clock_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
    parameters=[{'use_sim_time': True}],
)

# 关节状态桥接
joint_states_bridge = Node(
    package='ros_gz_bridge',
    executable='parameter_bridge',
    arguments=['/world/marm/model/marm/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model'],
    remappings=[('/world/marm/model/marm/joint_state', '/joint_states')],
    parameters=[{'use_sim_time': True}],
)

# MoveIt - 延迟启动确保时钟桥接先运行
move_group_launch = IncludeLaunchDescription(
    os.path.join(get_package_share_directory(MOVEIT_PACKAGE), "launch", "move_group.launch.py"),
    launch_arguments={"use_sim_time": use_sim_time}.items(),
)

move_group = TimerAction(
    period=3.0,
    actions=[move_group_launch]
)
```

## 验证方法

### 重新构建工作空间

```bash
colcon build --packages-select marm marm_moveit_config
source install/setup.bash
```

### 启动系统

```bash
ros2 launch marm gazebo_moveit_bringup.launch.py
```

### 验证步骤

1. **检查 use_sim_time 参数**：

```bash
ros2 param get /move_group use_sim_time
```

**预期结果**：`Boolean value is: True`

2. **检查时钟同步**：

```bash
ros2 topic echo /clock --once
ros2 topic echo /joint_states --once
```

**预期结果**：两个话题的时间戳应该在相近的范围内（差异 < 5秒）

3. **检查 TF 树**：

```bash
ros2 run tf2_tools view_frames
```

**预期结果**：所有变换正常，most_recent_transform 和 oldest_transform 时间接近

4. **检查控制器状态**：

```bash
ros2 control list_controllers
```

**预期结果**：

```
joint_state_broadcaster   active
arm_controller           active
gripper_controller       active
```

5. **测试运动规划**：在 RViz 中尝试执行运动规划，应该能够正常执行

## 核心问题总结

`generate_move_group_launch()` 函数内部创建 `move_group_params` 列表时，没有包含 `use_sim_time` 参数。因此需要在 launch 文件中手动添加参数设置逻辑，通过延迟执行 `ros2 param set` 命令来确保 MoveGroup 使用仿真时间。

## 相关错误信息

- `Didn't receive robot state (joint angles) with recent timestamp within 1.000000 seconds`
- `Check clock synchronization if your are running ROS across multiple machines!`
- `Failed to validate trajectory: couldn't receive full current joint state within 1s`
- `Execution completed: PREEMPTED`
- `Detected jump back in time. Clearing TF buffer.`
- `MoveGroupInterface::execute() failed or timeout reached`
