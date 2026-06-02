cmake_minimum_required(VERSION 3.8)
project(marm_control_pkg)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# uncomment the following section in order to fill in
# further dependencies manually.
# find_package(<dependency> REQUIRED)
find_package(rclcpp REQUIRED)
find_package(moveit_core REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

add_executable(arm_control_cpp_node src/arm_control_cpp_node.cpp)
add_executable(pose_control_cpp_node src/pose_control_cpp_node.cpp)

ament_target_dependencies(arm_control_cpp_node
  rclcpp
  moveit_core
  moveit_ros_planning_interface
  moveit_msgs
)

ament_target_dependencies(pose_control_cpp_node
  rclcpp
  moveit_core
  moveit_ros_planning_interface
  moveit_msgs
  tf2
  tf2_geometry_msgs
  geometry_msgs
)

install(TARGETS
  arm_control_cpp_node
  pose_control_cpp_node
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
