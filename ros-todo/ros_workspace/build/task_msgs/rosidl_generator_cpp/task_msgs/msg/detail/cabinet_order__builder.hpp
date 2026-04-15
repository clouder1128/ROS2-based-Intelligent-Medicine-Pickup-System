// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from task_msgs:msg/CabinetOrder.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_order.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_ORDER__BUILDER_HPP_
#define TASK_MSGS__MSG__DETAIL__CABINET_ORDER__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "task_msgs/msg/detail/cabinet_order__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace task_msgs
{

namespace msg
{

namespace builder
{

class Init_CabinetOrder_medicine_list
{
public:
  explicit Init_CabinetOrder_medicine_list(::task_msgs::msg::CabinetOrder & msg)
  : msg_(msg)
  {}
  ::task_msgs::msg::CabinetOrder medicine_list(::task_msgs::msg::CabinetOrder::_medicine_list_type arg)
  {
    msg_.medicine_list = std::move(arg);
    return std::move(msg_);
  }

private:
  ::task_msgs::msg::CabinetOrder msg_;
};

class Init_CabinetOrder_cabinet_id
{
public:
  Init_CabinetOrder_cabinet_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_CabinetOrder_medicine_list cabinet_id(::task_msgs::msg::CabinetOrder::_cabinet_id_type arg)
  {
    msg_.cabinet_id = std::move(arg);
    return Init_CabinetOrder_medicine_list(msg_);
  }

private:
  ::task_msgs::msg::CabinetOrder msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::task_msgs::msg::CabinetOrder>()
{
  return task_msgs::msg::builder::Init_CabinetOrder_cabinet_id();
}

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_ORDER__BUILDER_HPP_
