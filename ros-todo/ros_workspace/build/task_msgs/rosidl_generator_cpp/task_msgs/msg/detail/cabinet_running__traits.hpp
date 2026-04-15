// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from task_msgs:msg/CabinetRunning.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_running.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__TRAITS_HPP_
#define TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "task_msgs/msg/detail/cabinet_running__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace task_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const CabinetRunning & msg,
  std::ostream & out)
{
  out << "{";
  // member: cabinet_id
  {
    out << "cabinet_id: ";
    rosidl_generator_traits::value_to_yaml(msg.cabinet_id, out);
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
  const CabinetRunning & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: cabinet_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "cabinet_id: ";
    rosidl_generator_traits::value_to_yaml(msg.cabinet_id, out);
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

inline std::string to_yaml(const CabinetRunning & msg, bool use_flow_style = false)
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
  const task_msgs::msg::CabinetRunning & msg,
  std::ostream & out, size_t indentation = 0)
{
  task_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use task_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const task_msgs::msg::CabinetRunning & msg)
{
  return task_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<task_msgs::msg::CabinetRunning>()
{
  return "task_msgs::msg::CabinetRunning";
}

template<>
inline const char * name<task_msgs::msg::CabinetRunning>()
{
  return "task_msgs/msg/CabinetRunning";
}

template<>
struct has_fixed_size<task_msgs::msg::CabinetRunning>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<task_msgs::msg::CabinetRunning>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<task_msgs::msg::CabinetRunning>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__TRAITS_HPP_
