// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from task_msgs:msg/MedicineData.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "task_msgs/msg/detail/medicine_data__functions.h"
#include "task_msgs/msg/detail/medicine_data__struct.hpp"
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

void MedicineData_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) task_msgs::msg::MedicineData(_init);
}

void MedicineData_fini_function(void * message_memory)
{
  auto typed_message = static_cast<task_msgs::msg::MedicineData *>(message_memory);
  typed_message->~MedicineData();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember MedicineData_message_member_array[3] = {
  {
    "row",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs::msg::MedicineData, row),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "column",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs::msg::MedicineData, column),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "count",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs::msg::MedicineData, count),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers MedicineData_message_members = {
  "task_msgs::msg",  // message namespace
  "MedicineData",  // message name
  3,  // number of fields
  sizeof(task_msgs::msg::MedicineData),
  false,  // has_any_key_member_
  MedicineData_message_member_array,  // message members
  MedicineData_init_function,  // function to initialize message memory (memory has to be allocated)
  MedicineData_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t MedicineData_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &MedicineData_message_members,
  get_message_typesupport_handle_function,
  &task_msgs__msg__MedicineData__get_type_hash,
  &task_msgs__msg__MedicineData__get_type_description,
  &task_msgs__msg__MedicineData__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace task_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<task_msgs::msg::MedicineData>()
{
  return &::task_msgs::msg::rosidl_typesupport_introspection_cpp::MedicineData_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, task_msgs, msg, MedicineData)() {
  return &::task_msgs::msg::rosidl_typesupport_introspection_cpp::MedicineData_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
