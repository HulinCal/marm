#!/usr/bin/env python3
import os
import subprocess
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess

from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    # 桥接节点（转发 /clock）
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
        output='screen'
    )

    # 声明gui参数，默认值为true（启动GUI）
    gui_arg = DeclareLaunchArgument(
        'gui',
        default_value='false',
        description='Whether to start joint_state_publisher_gui'
    )

    # joint_state_publisher_gui节点
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        condition=IfCondition(LaunchConfiguration('gui'))
    )

    # 获取包的路径
    pkg_marm = get_package_share_directory('marm')
    
    # URDF文件路径
    urdf_path = os.path.join(pkg_marm, 'urdf', 'arm.urdf.xacro')
    # urdf_path = os.path.join(pkg_marm, 'urdf', 'm1.xacro')
    
    # 使用xacro处理urdf文件
    xacro_process = subprocess.run(
        ['xacro', urdf_path],
        capture_output=True,
        text=True
    )
    robot_description = xacro_process.stdout
    
    # 构建launch描述
    return LaunchDescription([
        gui_arg,
        clock_bridge,

        # 运行robot_state_publisher节点
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{'robot_description': robot_description, 'use_sim_time': True}]
        ),

        # 运行joint_state_publisher节点（当不使用GUI时）
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': True}],
            condition=IfCondition(LaunchConfiguration('gui', default='false'))
        ),

        joint_state_publisher_gui_node,

        # 运行gazebo，加载空世界
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', 'empty.sdf'],
            output='screen'
        ),

        # 在gazebo中spawn机器人模型
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-name', 'marm', '-topic', 'robot_description'],
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),

        # 加载并激活控制器
        ExecuteProcess(
            cmd=['bash', '-c',
                 'sleep 10 && '
                 'ros2 service call /controller_manager/load_controller controller_manager_msgs/srv/LoadController "{name: arm_controller}" && '
                 'ros2 service call /controller_manager/load_controller controller_manager_msgs/srv/LoadController "{name: gripper_controller}" && '
                 'ros2 service call /controller_manager/load_controller controller_manager_msgs/srv/LoadController "{name: joint_state_broadcaster}" && '
                 'ros2 service call /controller_manager/configure_controller controller_manager_msgs/srv/ConfigureController "{name: arm_controller}" && '
                 'ros2 service call /controller_manager/configure_controller controller_manager_msgs/srv/ConfigureController "{name: gripper_controller}" && '
                 'ros2 service call /controller_manager/configure_controller controller_manager_msgs/srv/ConfigureController "{name: joint_state_broadcaster}" && '
                 'ros2 service call /controller_manager/switch_controller controller_manager_msgs/srv/SwitchController "{activate_controllers: [\"arm_controller\", \"gripper_controller\", \"joint_state_broadcaster\"], deactivate_controllers: [], strictness: 2, activate_asap: false, timeout: {sec: 5, nanosec: 0}}"'],
            output='screen'
        ),

        # # 运行rviz2
        # ExecuteProcess(
        #     cmd=['rviz2'],
        #     output='screen'
        # )
    ])
