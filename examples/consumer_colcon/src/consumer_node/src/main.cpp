#include <memory>

#include <rclcpp/rclcpp.hpp>
#include <dummy_lib/print.hpp>

int main(int argc, char ** argv)
{
  dummy_lib::print_hello();

  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("colcon_consumer_node");
  RCLCPP_INFO(node->get_logger(), "colcon consumer_node: rclcpp linked and node started.");
  rclcpp::shutdown();
  return 0;
}
