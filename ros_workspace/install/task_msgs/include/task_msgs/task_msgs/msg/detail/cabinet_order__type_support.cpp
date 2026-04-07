// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from task_msgs:msg/CabinetOrder.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "task_msgs/msg/detail/cabinet_order__functions.h"
#include "task_msgs/msg/detail/cabinet_order__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace task_msgs
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void CabinetOrder_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) task_msgs::msg::CabinetOrder(_init);
}

void CabinetOrder_fini_function(void * message_memory)
{
  auto typed_message = static_cast<task_msgs::msg::CabinetOrder *>(message_memory);
  typed_message->~CabinetOrder();
}

size_t size_function__CabinetOrder__medicine_list(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<task_msgs::msg::MedicineData> *>(untyped_member);
  return member->size();
}

const void * get_const_function__CabinetOrder__medicine_list(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<task_msgs::msg::MedicineData> *>(untyped_member);
  return &member[index];
}

void * get_function__CabinetOrder__medicine_list(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<task_msgs::msg::MedicineData> *>(untyped_member);
  return &member[index];
}

void fetch_function__CabinetOrder__medicine_list(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const auto & item = *reinterpret_cast<const task_msgs::msg::MedicineData *>(
    get_const_function__CabinetOrder__medicine_list(untyped_member, index));
  auto & value = *reinterpret_cast<task_msgs::msg::MedicineData *>(untyped_value);
  value = item;
}

void assign_function__CabinetOrder__medicine_list(
  void * untyped_member, size_t index, const void * untyped_value)
{
  auto & item = *reinterpret_cast<task_msgs::msg::MedicineData *>(
    get_function__CabinetOrder__medicine_list(untyped_member, index));
  const auto & value = *reinterpret_cast<const task_msgs::msg::MedicineData *>(untyped_value);
  item = value;
}

void resize_function__CabinetOrder__medicine_list(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<task_msgs::msg::MedicineData> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember CabinetOrder_message_member_array[2] = {
  {
    "cabinet_id",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs::msg::CabinetOrder, cabinet_id),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "medicine_list",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<task_msgs::msg::MedicineData>(),  // members of sub message
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs::msg::CabinetOrder, medicine_list),  // bytes offset in struct
    nullptr,  // default value
    size_function__CabinetOrder__medicine_list,  // size() function pointer
    get_const_function__CabinetOrder__medicine_list,  // get_const(index) function pointer
    get_function__CabinetOrder__medicine_list,  // get(index) function pointer
    fetch_function__CabinetOrder__medicine_list,  // fetch(index, &value) function pointer
    assign_function__CabinetOrder__medicine_list,  // assign(index, value) function pointer
    resize_function__CabinetOrder__medicine_list  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers CabinetOrder_message_members = {
  "task_msgs::msg",  // message namespace
  "CabinetOrder",  // message name
  2,  // number of fields
  sizeof(task_msgs::msg::CabinetOrder),
  false,  // has_any_key_member_
  CabinetOrder_message_member_array,  // message members
  CabinetOrder_init_function,  // function to initialize message memory (memory has to be allocated)
  CabinetOrder_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t CabinetOrder_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &CabinetOrder_message_members,
  get_message_typesupport_handle_function,
  &task_msgs__msg__CabinetOrder__get_type_hash,
  &task_msgs__msg__CabinetOrder__get_type_description,
  &task_msgs__msg__CabinetOrder__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace task_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<task_msgs::msg::CabinetOrder>()
{
  return &::task_msgs::msg::rosidl_typesupport_introspection_cpp::CabinetOrder_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, task_msgs, msg, CabinetOrder)() {
  return &::task_msgs::msg::rosidl_typesupport_introspection_cpp::CabinetOrder_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
