#include <memory>

#include <rclcpp/rclcpp.hpp>

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("conan_test_package_node");
  RCLCPP_INFO(node->get_logger(), "Conan test_package: rclcpp linked and node started.");
  rclcpp::shutdown();
  return 0;
}
