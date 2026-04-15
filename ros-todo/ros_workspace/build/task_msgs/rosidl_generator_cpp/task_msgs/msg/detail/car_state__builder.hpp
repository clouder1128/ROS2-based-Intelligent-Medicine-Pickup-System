// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from task_msgs:msg/CarState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/car_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CAR_STATE__BUILDER_HPP_
#define TASK_MSGS__MSG__DETAIL__CAR_STATE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "task_msgs/msg/detail/car_state__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace task_msgs
{

namespace msg
{

namespace builder
{

class Init_CarState_isrunning
{
public:
  explicit Init_CarState_isrunning(::task_msgs::msg::CarState & msg)
  : msg_(msg)
  {}
  ::task_msgs::msg::CarState isrunning(::task_msgs::msg::CarState::_isrunning_type arg)
  {
    msg_.isrunning = std::move(arg);
    return std::move(msg_);
  }

private:
  ::task_msgs::msg::CarState msg_;
};

class Init_CarState_y
{
public:
  explicit Init_CarState_y(::task_msgs::msg::CarState & msg)
  : msg_(msg)
  {}
  Init_CarState_isrunning y(::task_msgs::msg::CarState::_y_type arg)
  {
    msg_.y = std::move(arg);
    return Init_CarState_isrunning(msg_);
  }

private:
  ::task_msgs::msg::CarState msg_;
};

class Init_CarState_x
{
public:
  explicit Init_CarState_x(::task_msgs::msg::CarState & msg)
  : msg_(msg)
  {}
  Init_CarState_y x(::task_msgs::msg::CarState::_x_type arg)
  {
    msg_.x = std::move(arg);
    return Init_CarState_y(msg_);
  }

private:
  ::task_msgs::msg::CarState msg_;
};

class Init_CarState_car_id
{
public:
  Init_CarState_car_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_CarState_x car_id(::task_msgs::msg::CarState::_car_id_type arg)
  {
    msg_.car_id = std::move(arg);
    return Init_CarState_x(msg_);
  }

private:
  ::task_msgs::msg::CarState msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::task_msgs::msg::CarState>()
{
  return task_msgs::msg::builder::Init_CarState_car_id();
}

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__CAR_STATE__BUILDER_HPP_
