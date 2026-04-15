// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from task_msgs:msg/MedicineData.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/medicine_data.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__STRUCT_HPP_
#define TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__task_msgs__msg__MedicineData __attribute__((deprecated))
#else
# define DEPRECATED__task_msgs__msg__MedicineData __declspec(deprecated)
#endif

namespace task_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct MedicineData_
{
  using Type = MedicineData_<ContainerAllocator>;

  explicit MedicineData_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->row = 0;
      this->column = 0;
      this->count = 0;
    }
  }

  explicit MedicineData_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->row = 0;
      this->column = 0;
      this->count = 0;
    }
  }

  // field types and members
  using _row_type =
    uint8_t;
  _row_type row;
  using _column_type =
    uint8_t;
  _column_type column;
  using _count_type =
    uint8_t;
  _count_type count;

  // setters for named parameter idiom
  Type & set__row(
    const uint8_t & _arg)
  {
    this->row = _arg;
    return *this;
  }
  Type & set__column(
    const uint8_t & _arg)
  {
    this->column = _arg;
    return *this;
  }
  Type & set__count(
    const uint8_t & _arg)
  {
    this->count = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    task_msgs::msg::MedicineData_<ContainerAllocator> *;
  using ConstRawPtr =
    const task_msgs::msg::MedicineData_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<task_msgs::msg::MedicineData_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<task_msgs::msg::MedicineData_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::MedicineData_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::MedicineData_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::MedicineData_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::MedicineData_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<task_msgs::msg::MedicineData_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<task_msgs::msg::MedicineData_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__task_msgs__msg__MedicineData
    std::shared_ptr<task_msgs::msg::MedicineData_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__task_msgs__msg__MedicineData
    std::shared_ptr<task_msgs::msg::MedicineData_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const MedicineData_ & other) const
  {
    if (this->row != other.row) {
      return false;
    }
    if (this->column != other.column) {
      return false;
    }
    if (this->count != other.count) {
      return false;
    }
    return true;
  }
  bool operator!=(const MedicineData_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct MedicineData_

// alias to use template instance with default allocator
using MedicineData =
  task_msgs::msg::MedicineData_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__STRUCT_HPP_
