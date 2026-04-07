// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from task_msgs:msg/TaskState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/task_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__TASK_STATE__BUILDER_HPP_
#define TASK_MSGS__MSG__DETAIL__TASK_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "task_msgs/msg/detail/task_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace task_msgs
{

namespace msg
{

namespace builder
{

class Init_TaskState_car_id
{
public:
  explicit Init_TaskState_car_id(::task_msgs::msg::TaskState & msg)
  : msg_(msg)
  {}
  ::task_msgs::msg::TaskState car_id(::task_msgs::msg::TaskState::_car_id_type arg)
  {
    msg_.car_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::task_msgs::msg::TaskState msg_;
};

class Init_TaskState_task_state
{
public:
  explicit Init_TaskState_task_state(::task_msgs::msg::TaskState & msg)
  : msg_(msg)
  {}
  Init_TaskState_car_id task_state(::task_msgs::msg::TaskState::_task_state_type arg)
  {
    msg_.task_state = std::move(arg);
    return Init_TaskState_car_id(msg_);
  }

private:
  ::task_msgs::msg::TaskState msg_;
};

class Init_TaskState_taskid
{
public:
  Init_TaskState_taskid()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TaskState_task_state taskid(::task_msgs::msg::TaskState::_taskid_type arg)
  {
    msg_.taskid = std::move(arg);
    return Init_TaskState_task_state(msg_);
  }

private:
  ::task_msgs::msg::TaskState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::task_msgs::msg::TaskState>()
{
  return task_msgs::msg::builder::Init_TaskState_taskid();
}

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__TASK_STATE__BUILDER_HPP_
