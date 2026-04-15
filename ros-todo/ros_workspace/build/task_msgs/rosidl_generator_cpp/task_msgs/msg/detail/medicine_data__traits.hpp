// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from task_msgs:msg/MedicineData.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/medicine_data.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__TRAITS_HPP_
#define TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "task_msgs/msg/detail/medicine_data__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace task_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const MedicineData & msg,
  std::ostream & out)
{
  out << "{";
  // member: row
  {
    out << "row: ";
    rosidl_generator_traits::value_to_yaml(msg.row, out);
    out << ", ";
  }

  // member: column
  {
    out << "column: ";
    rosidl_generator_traits::value_to_yaml(msg.column, out);
    out << ", ";
  }

  // member: count
  {
    out << "count: ";
    rosidl_generator_traits::value_to_yaml(msg.count, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const MedicineData & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: row
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "row: ";
    rosidl_generator_traits::value_to_yaml(msg.row, out);
    out << "\n";
  }

  // member: column
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "column: ";
    rosidl_generator_traits::value_to_yaml(msg.column, out);
    out << "\n";
  }

  // member: count
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "count: ";
    rosidl_generator_traits::value_to_yaml(msg.count, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const MedicineData & msg, bool use_flow_style = false)
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
  const task_msgs::msg::MedicineData & msg,
  std::ostream & out, size_t indentation = 0)
{
  task_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use task_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const task_msgs::msg::MedicineData & msg)
{
  return task_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<task_msgs::msg::MedicineData>()
{
  return "task_msgs::msg::MedicineData";
}

template<>
inline const char * name<task_msgs::msg::MedicineData>()
{
  return "task_msgs/msg/MedicineData";
}

template<>
struct has_fixed_size<task_msgs::msg::MedicineData>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<task_msgs::msg::MedicineData>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<task_msgs::msg::MedicineData>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__TRAITS_HPP_
