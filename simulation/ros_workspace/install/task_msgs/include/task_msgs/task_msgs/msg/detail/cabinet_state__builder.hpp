// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from task_msgs:msg/CabinetState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_STATE__BUILDER_HPP_
#define TASK_MSGS__MSG__DETAIL__CABINET_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "task_msgs/msg/detail/cabinet_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace task_msgs
{

namespace msg
{

namespace builder
{

class Init_CabinetState_medicine_list
{
public:
  explicit Init_CabinetState_medicine_list(::task_msgs::msg::CabinetState & msg)
  : msg_(msg)
  {}
  ::task_msgs::msg::CabinetState medicine_list(::task_msgs::msg::CabinetState::_medicine_list_type arg)
  {
    msg_.medicine_list = std::move(arg);
    return std::move(msg_);
  }

private:
  ::task_msgs::msg::CabinetState msg_;
};

class Init_CabinetState_cabinet_id
{
public:
  Init_CabinetState_cabinet_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_CabinetState_medicine_list cabinet_id(::task_msgs::msg::CabinetState::_cabinet_id_type arg)
  {
    msg_.cabinet_id = std::move(arg);
    return Init_CabinetState_medicine_list(msg_);
  }

private:
  ::task_msgs::msg::CabinetState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::task_msgs::msg::CabinetState>()
{
  return task_msgs::msg::builder::Init_CabinetState_cabinet_id();
}

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_STATE__BUILDER_HPP_
