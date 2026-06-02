//根据关节角度控制机器人运动

#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.hpp>

using namespace std::placeholders;
using MoveGroupInterface = moveit::planning_interface::MoveGroupInterface;

int main(int argc, char *argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("arm_control_cpp_node");

  // 【必须和你的 MoveIt 配置一致】
  static const std::string PLANNING_GROUP = "arm";

  // 创建 MoveIt 接口
  MoveGroupInterface move_group(node, PLANNING_GROUP);
  moveit::planning_interface::PlanningSceneInterface planning_scene_interface;

  // 设置规划时间
  move_group.setPlanningTime(5.0);
  move_group.setMaxVelocityScalingFactor(1.0);
  move_group.setMaxAccelerationScalingFactor(1.0);

  // ------------------------------
  // 目标关节角度（和你命令一致）
  // ------------------------------
  std::vector<double> target_joints = {
    0.5, 0.5, 0.5, 0.5, 0.5, 0.5
  };

  // 设置关节目标
  move_group.setJointValueTarget(target_joints);

  // ------------------------------
  // 1. 规划路径
  // ------------------------------
  MoveGroupInterface::Plan my_plan;
  bool success = (move_group.plan(my_plan) == moveit::core::MoveItErrorCode::SUCCESS);

  RCLCPP_INFO(node->get_logger(), "规划结果: %s", success ? "成功" : "失败");

  // ------------------------------
  // 2. 执行运动
  // ------------------------------
  if (success)
  {
    RCLCPP_INFO(node->get_logger(), "开始执行...");
    move_group.execute(my_plan);
    RCLCPP_INFO(node->get_logger(), "✅ 运动完成！");
  }
  else
  {
    RCLCPP_ERROR(node->get_logger(), "❌ 规划失败！");
  }

  rclcpp::shutdown();
  return 0;
}
