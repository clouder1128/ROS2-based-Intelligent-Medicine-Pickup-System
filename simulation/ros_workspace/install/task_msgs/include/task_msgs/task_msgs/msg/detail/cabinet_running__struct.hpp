// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from task_msgs:msg/CabinetRunning.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_running.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__STRUCT_HPP_
#define TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__task_msgs__msg__CabinetRunning __attribute__((deprecated))
#else
# define DEPRECATED__task_msgs__msg__CabinetRunning __declspec(deprecated)
#endif

namespace task_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct CabinetRunning_
{
  using Type = CabinetRunning_<ContainerAllocator>;

  explicit CabinetRunning_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->cabinet_id = 0;
      this->isrunning = 0;
    }
  }

  explicit CabinetRunning_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->cabinet_id = 0;
      this->isrunning = 0;
    }
  }

  // field types and members
  using _cabinet_id_type =
    uint8_t;
  _cabinet_id_type cabinet_id;
  using _isrunning_type =
    uint8_t;
  _isrunning_type isrunning;

  // setters for named parameter idiom
  Type & set__cabinet_id(
    const uint8_t & _arg)
  {
    this->cabinet_id = _arg;
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
    task_msgs::msg::CabinetRunning_<ContainerAllocator> *;
  using ConstRawPtr =
    const task_msgs::msg::CabinetRunning_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<task_msgs::msg::CabinetRunning_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<task_msgs::msg::CabinetRunning_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::CabinetRunning_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::CabinetRunning_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::CabinetRunning_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::CabinetRunning_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<task_msgs::msg::CabinetRunning_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<task_msgs::msg::CabinetRunning_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__task_msgs__msg__CabinetRunning
    std::shared_ptr<task_msgs::msg::CabinetRunning_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__task_msgs__msg__CabinetRunning
    std::shared_ptr<task_msgs::msg::CabinetRunning_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const CabinetRunning_ & other) const
  {
    if (this->cabinet_id != other.cabinet_id) {
      return false;
    }
    if (this->isrunning != other.isrunning) {
      return false;
    }
    return true;
  }
  bool operator!=(const CabinetRunning_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct CabinetRunning_

// alias to use template instance with default allocator
using CabinetRunning =
  task_msgs::msg::CabinetRunning_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__STRUCT_HPP_
