// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from task_msgs:msg/CabinetState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_STATE__TRAITS_HPP_
#define TASK_MSGS__MSG__DETAIL__CABINET_STATE__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "task_msgs/msg/detail/cabinet_state__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'medicine_list'
#include "task_msgs/msg/detail/medicine_data__traits.hpp"

namespace task_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const CabinetState & msg,
  std::ostream & out)
{
  out << "{";
  // member: cabinet_id
  {
    out << "cabinet_id: ";
    rosidl_generator_traits::value_to_yaml(msg.cabinet_id, out);
    out << ", ";
  }

  // member: medicine_list
  {
    if (msg.medicine_list.size() == 0) {
      out << "medicine_list: []";
    } else {
      out << "medicine_list: [";
      size_t pending_items = msg.medicine_list.size();
      for (auto item : msg.medicine_list) {
        to_flow_style_yaml(item, out);
        if (--pending_items > 0) {
          out << ", ";
        }
      }
      out << "]";
    }
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const CabinetState & msg,
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

  // member: medicine_list
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    if (msg.medicine_list.size() == 0) {
      out << "medicine_list: []\n";
    } else {
      out << "medicine_list:\n";
      for (auto item : msg.medicine_list) {
        if (indentation > 0) {
          out << std::string(indentation, ' ');
        }
        out << "-\n";
        to_block_style_yaml(item, out, indentation + 2);
      }
    }
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const CabinetState & msg, bool use_flow_style = false)
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
  const task_msgs::msg::CabinetState & msg,
  std::ostream & out, size_t indentation = 0)
{
  task_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use task_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const task_msgs::msg::CabinetState & msg)
{
  return task_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<task_msgs::msg::CabinetState>()
{
  return "task_msgs::msg::CabinetState";
}

template<>
inline const char * name<task_msgs::msg::CabinetState>()
{
  return "task_msgs/msg/CabinetState";
}

template<>
struct has_fixed_size<task_msgs::msg::CabinetState>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<task_msgs::msg::CabinetState>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<task_msgs::msg::CabinetState>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_STATE__TRAITS_HPP_
