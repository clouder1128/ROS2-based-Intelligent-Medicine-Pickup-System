// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from task_msgs:msg/MedicineData.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/medicine_data.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__BUILDER_HPP_
#define TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "task_msgs/msg/detail/medicine_data__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace task_msgs
{

namespace msg
{

namespace builder
{

class Init_MedicineData_count
{
public:
  explicit Init_MedicineData_count(::task_msgs::msg::MedicineData & msg)
  : msg_(msg)
  {}
  ::task_msgs::msg::MedicineData count(::task_msgs::msg::MedicineData::_count_type arg)
  {
    msg_.count = std::move(arg);
    return std::move(msg_);
  }

private:
  ::task_msgs::msg::MedicineData msg_;
};

class Init_MedicineData_column
{
public:
  explicit Init_MedicineData_column(::task_msgs::msg::MedicineData & msg)
  : msg_(msg)
  {}
  Init_MedicineData_count column(::task_msgs::msg::MedicineData::_column_type arg)
  {
    msg_.column = std::move(arg);
    return Init_MedicineData_count(msg_);
  }

private:
  ::task_msgs::msg::MedicineData msg_;
};

class Init_MedicineData_row
{
public:
  Init_MedicineData_row()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_MedicineData_column row(::task_msgs::msg::MedicineData::_row_type arg)
  {
    msg_.row = std::move(arg);
    return Init_MedicineData_column(msg_);
  }

private:
  ::task_msgs::msg::MedicineData msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::task_msgs::msg::MedicineData>()
{
  return task_msgs::msg::builder::Init_MedicineData_row();
}

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__BUILDER_HPP_
