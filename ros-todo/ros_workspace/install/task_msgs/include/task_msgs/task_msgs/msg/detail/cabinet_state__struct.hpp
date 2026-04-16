// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from task_msgs:msg/CabinetState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_state.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_STATE__STRUCT_HPP_
#define TASK_MSGS__MSG__DETAIL__CABINET_STATE__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'medicine_list'
#include "task_msgs/msg/detail/medicine_data__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__task_msgs__msg__CabinetState __attribute__((deprecated))
#else
# define DEPRECATED__task_msgs__msg__CabinetState __declspec(deprecated)
#endif

namespace task_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct CabinetState_
{
  using Type = CabinetState_<ContainerAllocator>;

  explicit CabinetState_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->cabinet_id = 0;
    }
  }

  explicit CabinetState_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->cabinet_id = 0;
    }
  }

  // field types and members
  using _cabinet_id_type =
    uint8_t;
  _cabinet_id_type cabinet_id;
  using _medicine_list_type =
    std::vector<task_msgs::msg::MedicineData_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<task_msgs::msg::MedicineData_<ContainerAllocator>>>;
  _medicine_list_type medicine_list;

  // setters for named parameter idiom
  Type & set__cabinet_id(
    const uint8_t & _arg)
  {
    this->cabinet_id = _arg;
    return *this;
  }
  Type & set__medicine_list(
    const std::vector<task_msgs::msg::MedicineData_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<task_msgs::msg::MedicineData_<ContainerAllocator>>> & _arg)
  {
    this->medicine_list = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    task_msgs::msg::CabinetState_<ContainerAllocator> *;
  using ConstRawPtr =
    const task_msgs::msg::CabinetState_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<task_msgs::msg::CabinetState_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<task_msgs::msg::CabinetState_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::CabinetState_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::CabinetState_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::CabinetState_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::CabinetState_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<task_msgs::msg::CabinetState_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<task_msgs::msg::CabinetState_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__task_msgs__msg__CabinetState
    std::shared_ptr<task_msgs::msg::CabinetState_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__task_msgs__msg__CabinetState
    std::shared_ptr<task_msgs::msg::CabinetState_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const CabinetState_ & other) const
  {
    if (this->cabinet_id != other.cabinet_id) {
      return false;
    }
    if (this->medicine_list != other.medicine_list) {
      return false;
    }
    return true;
  }
  bool operator!=(const CabinetState_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct CabinetState_

// alias to use template instance with default allocator
using CabinetState =
  task_msgs::msg::CabinetState_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_STATE__STRUCT_HPP_
