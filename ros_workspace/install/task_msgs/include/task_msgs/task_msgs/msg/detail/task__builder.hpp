// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from task_msgs:msg/Task.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/task.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__TASK__BUILDER_HPP_
#define TASK_MSGS__MSG__DETAIL__TASK__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "task_msgs/msg/detail/task__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace task_msgs
{

namespace msg
{

namespace builder
{

class Init_Task_type
{
public:
  explicit Init_Task_type(::task_msgs::msg::Task & msg)
  : msg_(msg)
  {}
  ::task_msgs::msg::Task type(::task_msgs::msg::Task::_type_type arg)
  {
    msg_.type = std::move(arg);
    return std::move(msg_);
  }

private:
  ::task_msgs::msg::Task msg_;
};

class Init_Task_cabinets
{
public:
  explicit Init_Task_cabinets(::task_msgs::msg::Task & msg)
  : msg_(msg)
  {}
  Init_Task_type cabinets(::task_msgs::msg::Task::_cabinets_type arg)
  {
    msg_.cabinets = std::move(arg);
    return Init_Task_type(msg_);
  }

private:
  ::task_msgs::msg::Task msg_;
};

class Init_Task_task_id
{
public:
  Init_Task_task_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Task_cabinets task_id(::task_msgs::msg::Task::_task_id_type arg)
  {
    msg_.task_id = std::move(arg);
    return Init_Task_cabinets(msg_);
  }

private:
  ::task_msgs::msg::Task msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::task_msgs::msg::Task>()
{
  return task_msgs::msg::builder::Init_Task_task_id();
}

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__TASK__BUILDER_HPP_
