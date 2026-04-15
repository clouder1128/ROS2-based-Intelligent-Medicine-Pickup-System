// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from task_msgs:msg/TaskState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/task_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__TASK_STATE__STRUCT_HPP_
#define TASK_MSGS__MSG__DETAIL__TASK_STATE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__task_msgs__msg__TaskState __attribute__((deprecated))
#else
# define DEPRECATED__task_msgs__msg__TaskState __declspec(deprecated)
#endif

namespace task_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct TaskState_
{
  using Type = TaskState_<ContainerAllocator>;

  explicit TaskState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->taskid = "";
      this->task_state = 0l;
      this->car_id = 0l;
    }
  }

  explicit TaskState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : taskid(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->taskid = "";
      this->task_state = 0l;
      this->car_id = 0l;
    }
  }

  // field types and members
  using _taskid_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _taskid_type taskid;
  using _task_state_type =
    int32_t;
  _task_state_type task_state;
  using _car_id_type =
    int32_t;
  _car_id_type car_id;

  // setters for named parameter idiom
  Type & set__taskid(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->taskid = _arg;
    return *this;
  }
  Type & set__task_state(
    const int32_t & _arg)
  {
    this->task_state = _arg;
    return *this;
  }
  Type & set__car_id(
    const int32_t & _arg)
  {
    this->car_id = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    task_msgs::msg::TaskState_<ContainerAllocator> *;
  using ConstRawPtr =
    const task_msgs::msg::TaskState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<task_msgs::msg::TaskState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<task_msgs::msg::TaskState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::TaskState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::TaskState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::TaskState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::TaskState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<task_msgs::msg::TaskState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<task_msgs::msg::TaskState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__task_msgs__msg__TaskState
    std::shared_ptr<task_msgs::msg::TaskState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__task_msgs__msg__TaskState
    std::shared_ptr<task_msgs::msg::TaskState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const TaskState_ & other) const
  {
    if (this->taskid != other.taskid) {
      return false;
    }
    if (this->task_state != other.task_state) {
      return false;
    }
    if (this->car_id != other.car_id) {
      return false;
    }
    return true;
  }
  bool operator!=(const TaskState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct TaskState_

// alias to use template instance with default allocator
using TaskState =
  task_msgs::msg::TaskState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__TASK_STATE__STRUCT_HPP_
