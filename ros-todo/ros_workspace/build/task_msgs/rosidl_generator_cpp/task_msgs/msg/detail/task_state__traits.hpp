// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from task_msgs:msg/TaskState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/task_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__TASK_STATE__TRAITS_HPP_
#define TASK_MSGS__MSG__DETAIL__TASK_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "task_msgs/msg/detail/task_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace task_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const TaskState & msg,
  std::ostream & out)
{
  out << "{";
  // member: taskid
  {
    out << "taskid: ";
    rosidl_generator_traits::value_to_yaml(msg.taskid, out);
    out << ", ";
  }

  // member: task_state
  {
    out << "task_state: ";
    rosidl_generator_traits::value_to_yaml(msg.task_state, out);
    out << ", ";
  }

  // member: car_id
  {
    out << "car_id: ";
    rosidl_generator_traits::value_to_yaml(msg.car_id, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const TaskState & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: taskid
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "taskid: ";
    rosidl_generator_traits::value_to_yaml(msg.taskid, out);
    out << "\n";
  }

  // member: task_state
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "task_state: ";
    rosidl_generator_traits::value_to_yaml(msg.task_state, out);
    out << "\n";
  }

  // member: car_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "car_id: ";
    rosidl_generator_traits::value_to_yaml(msg.car_id, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const TaskState & msg, bool use_flow_style = false)
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
  const task_msgs::msg::TaskState & msg,
  std::ostream & out, size_t indentation = 0)
{
  task_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use task_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const task_msgs::msg::TaskState & msg)
{
  return task_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<task_msgs::msg::TaskState>()
{
  return "task_msgs::msg::TaskState";
}

template<>
inline const char * name<task_msgs::msg::TaskState>()
{
  return "task_msgs/msg/TaskState";
}

template<>
struct has_fixed_size<task_msgs::msg::TaskState>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<task_msgs::msg::TaskState>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<task_msgs::msg::TaskState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // TASK_MSGS__MSG__DETAIL__TASK_STATE__TRAITS_HPP_
