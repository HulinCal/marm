#include <rclcpp/rclcpp.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <trajectory_msgs/msg/joint_trajectory.hpp>
#include <thread>

using MoveGroupInterface = moveit::planning_interface::MoveGroupInterface;

int main(int argc, char *argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("arm_gripper_final_node");
  node->set_parameter(rclcpp::Parameter("use_sim_time", true));

  // ==========================
  // 1. 机械臂控制
  // ==========================
  MoveGroupInterface move_arm(node, "arm");
  move_arm.setPlanningTime(5.0);
  move_arm.setMaxVelocityScalingFactor(0.6);
  move_arm.setMaxAccelerationScalingFactor(0.6);

  // 回 HOME
  RCLCPP_INFO(node->get_logger(), "✅ 机械臂回 HOME");
  move_arm.setNamedTarget("home");
  MoveGroupInterface::Plan home_plan;
  if (move_arm.plan(home_plan)) move_arm.execute(home_plan);
  rclcpp::sleep_for(std::chrono::seconds(1));

  // 去目标点
  geometry_msgs::msg::PoseStamped target_pose;
  target_pose.header.frame_id = "base_link";
  target_pose.header.stamp = node->get_clock()->now();
  target_pose.pose.position.x = 0.14996;
  target_pose.pose.position.y = 0.18317;
  target_pose.pose.position.z = 0.41203;
  target_pose.pose.orientation.x = -0.59375;
  target_pose.pose.orientation.y = -0.60903;
  target_pose.pose.orientation.z = -0.13927;
  target_pose.pose.orientation.w = 0.5071;

  move_arm.setPoseTarget(target_pose, "grasping_frame");
  MoveGroupInterface::Plan arm_plan;
  if (move_arm.plan(arm_plan)) {
    move_arm.execute(arm_plan);
    RCLCPP_INFO(node->get_logger(), "✅ 机械臂到达目标！");
  }
  rclcpp::sleep_for(std::chrono::seconds(2));

  // ==============================================
  // 🔥 【终极稳定版】夹爪 闭合 → 等待 → 打开
  // ==============================================

  // 【1】创建发布者（只创建一次，最稳定）
  auto gripper_pub = node->create_publisher<trajectory_msgs::msg::JointTrajectory>("/gripper_controller/joint_trajectory", 10);
  rclcpp::sleep_for(std::chrono::milliseconds(500)); // 必须等连接建立

  // --------------------------------------------------------------------
  // 闭合指令
  // --------------------------------------------------------------------
  RCLCPP_INFO(node->get_logger(), "🚀 闭合夹爪...");
  trajectory_msgs::msg::JointTrajectory msg_close;
  msg_close.joint_names = {"finger_joint1"};
  msg_close.points.resize(1);
  msg_close.points[0].positions = {0.055};
  msg_close.points[0].time_from_start = rclcpp::Duration::from_seconds(0.8);
  gripper_pub->publish(msg_close);
  rclcpp::sleep_for(std::chrono::seconds(2)); // 等动作完成

  // --------------------------------------------------------------------
  // 打开指令（关键：重新构造一个全新消息！）
  // --------------------------------------------------------------------
  RCLCPP_INFO(node->get_logger(), "🚀 打开夹爪...");
  trajectory_msgs::msg::JointTrajectory msg_open; // 重新定义！
  msg_open.joint_names = {"finger_joint1"};
  msg_open.points.resize(1);
  msg_open.points[0].positions = {0.005};
  msg_open.points[0].time_from_start = rclcpp::Duration::from_seconds(0.8);
  gripper_pub->publish(msg_open);
  rclcpp::sleep_for(std::chrono::seconds(2));

  RCLCPP_INFO(node->get_logger(), "🎉 成功：闭合 → 打开！");
  rclcpp::shutdown();
  return 0;
}
