// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from task_msgs:msg/CabinetRunning.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_running.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__BUILDER_HPP_
#define TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "task_msgs/msg/detail/cabinet_running__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace task_msgs
{

namespace msg
{

namespace builder
{

class Init_CabinetRunning_isrunning
{
public:
  explicit Init_CabinetRunning_isrunning(::task_msgs::msg::CabinetRunning & msg)
  : msg_(msg)
  {}
  ::task_msgs::msg::CabinetRunning isrunning(::task_msgs::msg::CabinetRunning::_isrunning_type arg)
  {
    msg_.isrunning = std::move(arg);
    return std::move(msg_);
  }

private:
  ::task_msgs::msg::CabinetRunning msg_;
};

class Init_CabinetRunning_cabinet_id
{
public:
  Init_CabinetRunning_cabinet_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_CabinetRunning_isrunning cabinet_id(::task_msgs::msg::CabinetRunning::_cabinet_id_type arg)
  {
    msg_.cabinet_id = std::move(arg);
    return Init_CabinetRunning_isrunning(msg_);
  }

private:
  ::task_msgs::msg::CabinetRunning msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::task_msgs::msg::CabinetRunning>()
{
  return task_msgs::msg::builder::Init_CabinetRunning_cabinet_id();
}

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__BUILDER_HPP_
