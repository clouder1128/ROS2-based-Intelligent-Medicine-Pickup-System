// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from task_msgs:msg/CarState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/car_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CAR_STATE__STRUCT_HPP_
#define TASK_MSGS__MSG__DETAIL__CAR_STATE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__task_msgs__msg__CarState __attribute__((deprecated))
#else
# define DEPRECATED__task_msgs__msg__CarState __declspec(deprecated)
#endif

namespace task_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct CarState_
{
  using Type = CarState_<ContainerAllocator>;

  explicit CarState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->car_id = 0;
      this->x = 0.0f;
      this->y = 0.0f;
      this->isrunning = 0;
    }
  }

  explicit CarState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->car_id = 0;
      this->x = 0.0f;
      this->y = 0.0f;
      this->isrunning = 0;
    }
  }

  // field types and members
  using _car_id_type =
    uint8_t;
  _car_id_type car_id;
  using _x_type =
    float;
  _x_type x;
  using _y_type =
    float;
  _y_type y;
  using _isrunning_type =
    uint8_t;
  _isrunning_type isrunning;

  // setters for named parameter idiom
  Type & set__car_id(
    const uint8_t & _arg)
  {
    this->car_id = _arg;
    return *this;
  }
  Type & set__x(
    const float & _arg)
  {
    this->x = _arg;
    return *this;
  }
  Type & set__y(
    const float & _arg)
  {
    this->y = _arg;
    return *this;
  }
  Type & set__isrunning(
    const uint8_t & _arg)
  {
    this->isrunning = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    task_msgs::msg::CarState_<ContainerAllocator> *;
  using ConstRawPtr =
    const task_msgs::msg::CarState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<task_msgs::msg::CarState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<task_msgs::msg::CarState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::CarState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::CarState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::CarState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::CarState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<task_msgs::msg::CarState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<task_msgs::msg::CarState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__task_msgs__msg__CarState
    std::shared_ptr<task_msgs::msg::CarState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__task_msgs__msg__CarState
    std::shared_ptr<task_msgs::msg::CarState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const CarState_ & other) const
  {
    if (this->car_id != other.car_id) {
      return false;
    }
    if (this->x != other.x) {
      return false;
    }
    if (this->y != other.y) {
      return false;
    }
    if (this->isrunning != other.isrunning) {
      return false;
    }
    return true;
  }
  bool operator!=(const CarState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct CarState_

// alias to use template instance with default allocator
using CarState =
  task_msgs::msg::CarState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__CAR_STATE__STRUCT_HPP_
