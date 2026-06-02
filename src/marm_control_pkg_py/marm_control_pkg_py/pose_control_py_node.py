import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.duration import Duration
from geometry_msgs.msg import PoseStamped
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import PlanningOptions, Constraints, PositionConstraint, OrientationConstraint, RobotState
from moveit_msgs.srv import GetPlanningScene, GetMotionPlan
from shape_msgs.msg import SolidPrimitive
from sensor_msgs.msg import JointState
import time


class ArmGripperControl(Node):
    def __init__(self):
        super().__init__("arm_gripper_final_node")

        self.move_group_client = ActionClient(self, MoveGroup, "/move_action")

        self.gripper_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10
        )

    def wait_for_action_server(self, timeout_sec=10.0):
        if not self.move_group_client.wait_for_server(timeout_sec=timeout_sec):
            self.get_logger().error("move_group action server not available!")
            return False
        return True

    def move_to_named_target(self, target_name):
        self.get_logger().info(f"✅ 机械臂回 {target_name}")

        goal = MoveGroup.Goal()
        goal.request.group_name = "arm"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0

        goal.planning_options = PlanningOptions()
        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.plan_only = False

        self.get_logger().info("Sending goal to move_group...{target_name}")
        future = self.move_group_client.send_goal_async(goal)
        
        if not rclpy.spin_until_future_complete(self, future, timeout_sec=20.0):
            self.get_logger().error("Goal({target_name}) was rejected or timed out")
            return False
        
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f"Goal({target_name}) was rejected by move_group")
            return False
        
        self.get_logger().info(f"Goal({target_name}) accepted, waiting for result...")
        result_future = goal_handle.get_result_async()
        
        if not rclpy.spin_until_future_complete(self, result_future, timeout_sec=30.0):
            self.get_logger().error(f"Result({target_name}) timed out")
            return False
        
        result = result_future.result()
        if result.error_code.val == 1:
            self.get_logger().info(f"✅ 到达 {target_name} 成功！")
            return True
        else:
            self.get_logger().error(f"❌ 到达 {target_name} 失败: {result.error_code.val}")
            return False

    def move_to_pose_target(self, target_pose, end_effector_link="grasping_frame"):
        self.get_logger().info("🚀 移动到目标位姿...")

        goal = MoveGroup.Goal()
        goal.request.group_name = "arm"
        goal.request.num_planning_attempts = 10
        goal.request.allowed_planning_time = 5.0

        pos_constraint = PositionConstraint()
        pos_constraint.header.frame_id = "base_link"
        pos_constraint.link_name = end_effector_link

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [0.01, 0.01, 0.01]

        pos_constraint.constraint_region.primitives = [primitive]
        pos_constraint.constraint_region.primitive_poses = [target_pose.pose]

        ori_constraint = OrientationConstraint()
        ori_constraint.header.frame_id = "base_link"
        ori_constraint.link_name = end_effector_link
        ori_constraint.orientation = target_pose.pose.orientation
        ori_constraint.absolute_x_axis_tolerance = 0.01
        ori_constraint.absolute_y_axis_tolerance = 0.01
        ori_constraint.absolute_z_axis_tolerance = 0.01
        ori_constraint.weight = 1.0

        constraint = Constraints()
        constraint.position_constraints = [pos_constraint]
        constraint.orientation_constraints = [ori_constraint]
        goal.request.goal_constraints = [constraint]

        goal.planning_options = PlanningOptions()
        goal.planning_options.planning_scene_diff.is_diff = True
        goal.planning_options.plan_only = False

        self.get_logger().info("Sending goal to move_group...")
        future = self.move_group_client.send_goal_async(goal)
        
        if not rclpy.spin_until_future_complete(self, future, timeout_sec=20.0):
            self.get_logger().error(f"move_to_pose_target：Goal was rejected or timed out")
            return False
        
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f"move_to_pose_target： Goal was rejected by move_group")
            return False
        
        self.get_logger().info(f"move_to_pose_target：Goal accepted, waiting for result...")
        result_future = goal_handle.get_result_async()
        
        if not rclpy.spin_until_future_complete(self, result_future, timeout_sec=30.0):
            self.get_logger().error("Result timed out")
            return False
        
        result = result_future.result()
        if result.error_code.val == 1:
            self.get_logger().info(f"move_to_pose_target：✅ 机械臂到达目标！")
            return True
        else:
            self.get_logger().error(f"move_to_pose_target：❌ 到达目标失败: {result.error_code.val}")
            return False

    def close_gripper(self):
        self.get_logger().info("🚀 闭合夹爪...")
        msg = JointTrajectory()
        msg.joint_names = ["finger_joint1"]
        point = JointTrajectoryPoint()
        point.positions = [0.02]
        point.time_from_start = Duration(seconds=2.0).to_msg()
        msg.points = [point]
        self.gripper_pub.publish(msg)

    def open_gripper(self):
        self.get_logger().info("🚀 打开夹爪...")
        msg = JointTrajectory()
        msg.joint_names = ["finger_joint1"]
        point = JointTrajectoryPoint()
        point.positions = [0.05]
        point.time_from_start = Duration(seconds=2.0).to_msg()
        msg.points = [point]
        self.gripper_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    node = ArmGripperControl()

    time.sleep(0.5)

    if not node.wait_for_action_server(timeout_sec=15.0):
        node.get_logger().error("无法连接到 move_action action server，请先启动: ros2 launch marm_moveit_config move_group.launch.py")
        rclpy.shutdown()
        return

    node.move_to_named_target("home")
    time.sleep(1)

    target_pose = PoseStamped()
    target_pose.header.frame_id = "base_link"
    target_pose.header.stamp = node.get_clock().now().to_msg()
    target_pose.pose.position.x = 0.14996
    target_pose.pose.position.y = 0.18317
    target_pose.pose.position.z = 0.41203
    target_pose.pose.orientation.x = -0.59375
    target_pose.pose.orientation.y = -0.60903
    target_pose.pose.orientation.z = -0.13927
    target_pose.pose.orientation.w = 0.5071

    node.move_to_pose_target(target_pose, "grasping_frame")
    time.sleep(2)

    node.close_gripper()
    time.sleep(20)

    node.open_gripper()
    time.sleep(2)

    node.get_logger().info("🎉 成功：闭合 → 打开！")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
