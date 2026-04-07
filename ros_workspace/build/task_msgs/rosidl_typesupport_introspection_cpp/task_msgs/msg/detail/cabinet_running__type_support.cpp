// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from task_msgs:msg/CabinetRunning.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "task_msgs/msg/detail/cabinet_running__functions.h"
#include "task_msgs/msg/detail/cabinet_running__struct.hpp"
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

void CabinetRunning_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) task_msgs::msg::CabinetRunning(_init);
}

void CabinetRunning_fini_function(void * message_memory)
{
  auto typed_message = static_cast<task_msgs::msg::CabinetRunning *>(message_memory);
  typed_message->~CabinetRunning();
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember CabinetRunning_message_member_array[2] = {
  {
    "cabinet_id",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs::msg::CabinetRunning, cabinet_id),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "isrunning",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs::msg::CabinetRunning, isrunning),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr,  // fetch(index, &value) function pointer
    nullptr,  // assign(index, value) function pointer
    nullptr  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers CabinetRunning_message_members = {
  "task_msgs::msg",  // message namespace
  "CabinetRunning",  // message name
  2,  // number of fields
  sizeof(task_msgs::msg::CabinetRunning),
  false,  // has_any_key_member_
  CabinetRunning_message_member_array,  // message members
  CabinetRunning_init_function,  // function to initialize message memory (memory has to be allocated)
  CabinetRunning_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t CabinetRunning_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &CabinetRunning_message_members,
  get_message_typesupport_handle_function,
  &task_msgs__msg__CabinetRunning__get_type_hash,
  &task_msgs__msg__CabinetRunning__get_type_description,
  &task_msgs__msg__CabinetRunning__get_type_description_sources,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace task_msgs


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<task_msgs::msg::CabinetRunning>()
{
  return &::task_msgs::msg::rosidl_typesupport_introspection_cpp::CabinetRunning_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, task_msgs, msg, CabinetRunning)() {
  return &::task_msgs::msg::rosidl_typesupport_introspection_cpp::CabinetRunning_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
