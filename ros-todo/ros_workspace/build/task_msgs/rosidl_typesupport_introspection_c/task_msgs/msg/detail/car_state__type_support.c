// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from task_msgs:msg/CarState.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "task_msgs/msg/detail/car_state__rosidl_typesupport_introspection_c.h"
#include "task_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "task_msgs/msg/detail/car_state__functions.h"
#include "task_msgs/msg/detail/car_state__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  task_msgs__msg__CarState__init(message_memory);
}

void task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_fini_function(void * message_memory)
{
  task_msgs__msg__CarState__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_message_member_array[4] = {
  {
    "car_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs__msg__CarState, car_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "x",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs__msg__CarState, x),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "y",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_FLOAT,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs__msg__CarState, y),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "isrunning",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs__msg__CarState, isrunning),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_message_members = {
  "task_msgs__msg",  // message namespace
  "CarState",  // message name
  4,  // number of fields
  sizeof(task_msgs__msg__CarState),
  false,  // has_any_key_member_
  task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_message_member_array,  // message members
  task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_init_function,  // function to initialize message memory (memory has to be allocated)
  task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_message_type_support_handle = {
  0,
  &task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_message_members,
  get_message_typesupport_handle_function,
  &task_msgs__msg__CarState__get_type_hash,
  &task_msgs__msg__CarState__get_type_description,
  &task_msgs__msg__CarState__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_task_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, task_msgs, msg, CarState)() {
  if (!task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_message_type_support_handle.typesupport_identifier) {
    task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &task_msgs__msg__CarState__rosidl_typesupport_introspection_c__CarState_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
