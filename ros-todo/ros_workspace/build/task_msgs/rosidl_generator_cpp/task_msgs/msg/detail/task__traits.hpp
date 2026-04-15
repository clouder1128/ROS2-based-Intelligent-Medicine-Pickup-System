// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from task_msgs:msg/Task.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/task.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__TASK__TRAITS_HPP_
#define TASK_MSGS__MSG__DETAIL__TASK__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "task_msgs/msg/detail/task__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'cabinets'
#include "task_msgs/msg/detail/cabinet_order__traits.hpp"

namespace task_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const Task & msg,
  std::ostream & out)
{
  out << "{";
  // member: task_id
  {
    out << "task_id: ";
    rosidl_generator_traits::value_to_yaml(msg.task_id, out);
    out << ", ";
  }

  // member: cabinets
  {
    if (msg.cabinets.size() == 0) {
      out << "cabinets: []";
    } else {
      out << "cabinets: [";
      size_t pending_items = msg.cabinets.size();
      for (auto item : msg.cabinets) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
    out << ", ";
  }

  // member: type
  {
    out << "type: ";
    rosidl_generator_traits::value_to_yaml(msg.type, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const Task & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: task_id
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "task_id: ";
    rosidl_generator_traits::value_to_yaml(msg.task_id, out);
    out << "\n";
  }

  // member: cabinets
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.cabinets.size() == 0) {
      out << "cabinets: []\n";
    } else {
      out << "cabinets:\n";
      for (auto item : msg.cabinets) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }

  // member: type
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "type: ";
    rosidl_generator_traits::value_to_yaml(msg.type, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const Task & msg, bool use_flow_style = false)
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
  const task_msgs::msg::Task & msg,
  std::ostream & out, size_t indentation = 0)
{
  task_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use task_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const task_msgs::msg::Task & msg)
{
  return task_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<task_msgs::msg::Task>()
{
  return "task_msgs::msg::Task";
}

template<>
inline const char * name<task_msgs::msg::Task>()
{
  return "task_msgs/msg/Task";
}

template<>
struct has_fixed_size<task_msgs::msg::Task>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<task_msgs::msg::Task>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<task_msgs::msg::Task>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // TASK_MSGS__MSG__DETAIL__TASK__TRAITS_HPP_
