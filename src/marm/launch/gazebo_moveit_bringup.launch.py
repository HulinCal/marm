import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # ====================== 你的配置 ======================
    ROBOT_NAME = "marm"
    MOVEIT_PACKAGE = "marm_moveit_config"
    GAZEBO_WORLD = "empty.sdf"
    # ======================================================

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    # 1. 启动 Gazebo
    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", GAZEBO_WORLD],
        output="screen",
        name="gazebo",
    )

    # 2. Spawn 机器人到 Gazebo
    spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-topic", "robot_description", "-name", ROBOT_NAME],
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    # 2. RSP - 注释掉，避免与下面的robot_state_publisher冲突--rsp.launch.py就是发布机器人描述
    # rsp = IncludeLaunchDescription(
    #     os.path.join(get_package_share_directory(MOVEIT_PACKAGE), "launch", "rsp.launch.py"),
    #     launch_arguments={"use_sim_time": use_sim_time}.items(),
    # )

    # 3. Robot State Publisher 发布机器人描述topic
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'robot_description': open(os.path.join(get_package_share_directory('marm'), 'urdf', 'arm.urdf')).read()}
        ],
    )

    # 4. 时钟桥，/clock和joint_states话题桥接
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model'  # 必须加关节桥
        ],
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'qos_overrides./joint_states.publisher.reliability': 'reliable'}  # 必须加QoS
        ]
    )

    # 5.控制器Spawner：启动关节状态广播器、臂控制器、夹爪控制器
    spawn_jsb = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        parameters=[{"use_sim_time": True}],
    )

    spawn_arm = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["arm_controller"],
        parameters=[{"use_sim_time": True}],
    )

    spawn_gripper = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller"],
        parameters=[{"use_sim_time": True}],
    )

    # 6. MoveIt + RViz
    # MoveIt - 延迟启动确保时钟桥接先运行
    move_group_launch = IncludeLaunchDescription(
        os.path.join(get_package_share_directory(MOVEIT_PACKAGE), "launch", "move_group.launch.py"),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    move_group = TimerAction(
        period=3.0,
        actions=[move_group_launch]
    )

    # 7. RViz - 启动 RViz
    rviz = IncludeLaunchDescription(
        os.path.join(get_package_share_directory(MOVEIT_PACKAGE), "launch", "moveit_rviz.launch.py"),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        gazebo,
        spawn_entity,

        robot_state_publisher,
        clock_bridge,

        spawn_jsb,
        spawn_arm,
        spawn_gripper,

        move_group,
        rviz,
    ])