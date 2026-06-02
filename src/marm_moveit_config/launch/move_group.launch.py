# from moveit_configs_utils import MoveItConfigsBuilder
# from moveit_configs_utils.launches import generate_move_group_launch

# def generate_launch_description():
#     moveit_config = MoveItConfigsBuilder("marm", package_name="marm_moveit_config").trajectory_execution().to_moveit_configs()
#     return generate_move_group_launch(moveit_config)


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