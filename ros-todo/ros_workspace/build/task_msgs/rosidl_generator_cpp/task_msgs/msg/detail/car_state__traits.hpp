// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from task_msgs:msg/CarState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/car_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CAR_STATE__TRAITS_HPP_
#define TASK_MSGS__MSG__DETAIL__CAR_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "task_msgs/msg/detail/car_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace task_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const CarState & msg,
  std::ostream & out)
{
  out << "{";
  // member: car_id
  {
    out << "car_id: ";
    rosidl_generator_traits::value_to_yaml(msg.car_id, out);
    out << ", ";
  }

  // member: x
  {
    out << "x: ";
    rosidl_generator_traits::value_to_yaml(msg.x, out);
    out << ", ";
  }

  // member: y
  {
    out << "y: ";
    rosidl_generator_traits::value_to_yaml(msg.y, out);
    out << ", ";
  }

  // member: isrunning
  {
    out << "isrunning: ";
    rosidl_generator_traits::value_to_yaml(msg.isrunning, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const CarState & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: car_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "car_id: ";
    rosidl_generator_traits::value_to_yaml(msg.car_id, out);
    out << "\n";
  }

  // member: x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "x: ";
    rosidl_generator_traits::value_to_yaml(msg.x, out);
    out << "\n";
  }

  // member: y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "y: ";
    rosidl_generator_traits::value_to_yaml(msg.y, out);
    out << "\n";
  }

  // member: isrunning
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "isrunning: ";
    rosidl_generator_traits::value_to_yaml(msg.isrunning, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const CarState & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace task_msgs

namespace rosidl_generator_traits
{

[[deprecated("use task_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const task_msgs::msg::CarState & msg,
  std::ostream & out, size_t indentation = 0)
{
  task_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use task_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const task_msgs::msg::CarState & msg)
{
  return task_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<task_msgs::msg::CarState>()
{
  return "task_msgs::msg::CarState";
}

template<>
inline const char * name<task_msgs::msg::CarState>()
{
  return "task_msgs/msg/CarState";
}

template<>
struct has_fixed_size<task_msgs::msg::CarState>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<task_msgs::msg::CarState>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<task_msgs::msg::CarState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // TASK_MSGS__MSG__DETAIL__CAR_STATE__TRAITS_HPP_
