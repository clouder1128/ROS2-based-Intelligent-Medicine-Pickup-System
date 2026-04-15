// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from task_msgs:msg/CabinetOrder.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_order.hpp"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_ORDER__STRUCT_HPP_
#define TASK_MSGS__MSG__DETAIL__CABINET_ORDER__STRUCT_HPP_

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
# define DEPRECATED__task_msgs__msg__CabinetOrder __attribute__((deprecated))
#else
# define DEPRECATED__task_msgs__msg__CabinetOrder __declspec(deprecated)
#endif

namespace task_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct CabinetOrder_
{
  using Type = CabinetOrder_<ContainerAllocator>;

  explicit CabinetOrder_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->cabinet_id = "";
    }
  }

  explicit CabinetOrder_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : cabinet_id(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->cabinet_id = "";
    }
  }

  // field types and members
  using _cabinet_id_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _cabinet_id_type cabinet_id;
  using _medicine_list_type =
    std::vector<task_msgs::msg::MedicineData_<ContainerAllocator>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<task_msgs::msg::MedicineData_<ContainerAllocator>>>;
  _medicine_list_type medicine_list;

  // setters for named parameter idiom
  Type & set__cabinet_id(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
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
    task_msgs::msg::CabinetOrder_<ContainerAllocator> *;
  using ConstRawPtr =
    const task_msgs::msg::CabinetOrder_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<task_msgs::msg::CabinetOrder_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<task_msgs::msg::CabinetOrder_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::CabinetOrder_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::CabinetOrder_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      task_msgs::msg::CabinetOrder_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<task_msgs::msg::CabinetOrder_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<task_msgs::msg::CabinetOrder_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<task_msgs::msg::CabinetOrder_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__task_msgs__msg__CabinetOrder
    std::shared_ptr<task_msgs::msg::CabinetOrder_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__task_msgs__msg__CabinetOrder
    std::shared_ptr<task_msgs::msg::CabinetOrder_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const CabinetOrder_ & other) const
  {
    if (this->cabinet_id != other.cabinet_id) {
      return false;
    }
    if (this->medicine_list != other.medicine_list) {
      return false;
    }
    return true;
  }
  bool operator!=(const CabinetOrder_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct CabinetOrder_

// alias to use template instance with default allocator
using CabinetOrder =
  task_msgs::msg::CabinetOrder_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace task_msgs

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_ORDER__STRUCT_HPP_
