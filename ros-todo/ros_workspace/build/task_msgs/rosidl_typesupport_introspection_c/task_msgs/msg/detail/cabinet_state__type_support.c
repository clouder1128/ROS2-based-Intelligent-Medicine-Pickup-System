// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from task_msgs:msg/CabinetState.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "task_msgs/msg/detail/cabinet_state__rosidl_typesupport_introspection_c.h"
#include "task_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "task_msgs/msg/detail/cabinet_state__functions.h"
#include "task_msgs/msg/detail/cabinet_state__struct.h"


// Include directives for member types
// Member `medicine_list`
#include "task_msgs/msg/medicine_data.h"
// Member `medicine_list`
#include "task_msgs/msg/detail/medicine_data__rosidl_typesupport_introspection_c.h"

#ifdef __cplusplus
extern "C"
{
#endif

void task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  task_msgs__msg__CabinetState__init(message_memory);
}

void task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_fini_function(void * message_memory)
{
  task_msgs__msg__CabinetState__fini(message_memory);
}

size_t task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__size_function__CabinetState__medicine_list(
  const void * untyped_member)
{
  const task_msgs__msg__MedicineData__Sequence * member =
    (const task_msgs__msg__MedicineData__Sequence *)(untyped_member);
  return member->size;
}

const void * task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__get_const_function__CabinetState__medicine_list(
  const void * untyped_member, size_t index)
{
  const task_msgs__msg__MedicineData__Sequence * member =
    (const task_msgs__msg__MedicineData__Sequence *)(untyped_member);
  return &member->data[index];
}

void * task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__get_function__CabinetState__medicine_list(
  void * untyped_member, size_t index)
{
  task_msgs__msg__MedicineData__Sequence * member =
    (task_msgs__msg__MedicineData__Sequence *)(untyped_member);
  return &member->data[index];
}

void task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__fetch_function__CabinetState__medicine_list(
  const void * untyped_member, size_t index, void * untyped_value)
{
  const task_msgs__msg__MedicineData * item =
    ((const task_msgs__msg__MedicineData *)
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__get_const_function__CabinetState__medicine_list(untyped_member, index));
  task_msgs__msg__MedicineData * value =
    (task_msgs__msg__MedicineData *)(untyped_value);
  *value = *item;
}

void task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__assign_function__CabinetState__medicine_list(
  void * untyped_member, size_t index, const void * untyped_value)
{
  task_msgs__msg__MedicineData * item =
    ((task_msgs__msg__MedicineData *)
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__get_function__CabinetState__medicine_list(untyped_member, index));
  const task_msgs__msg__MedicineData * value =
    (const task_msgs__msg__MedicineData *)(untyped_value);
  *item = *value;
}

bool task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__resize_function__CabinetState__medicine_list(
  void * untyped_member, size_t size)
{
  task_msgs__msg__MedicineData__Sequence * member =
    (task_msgs__msg__MedicineData__Sequence *)(untyped_member);
  task_msgs__msg__MedicineData__Sequence__fini(member);
  return task_msgs__msg__MedicineData__Sequence__init(member, size);
}

static rosidl_typesupport_introspection_c__MessageMember task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_member_array[2] = {
  {
    "cabinet_id",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is key
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs__msg__CabinetState, cabinet_id),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "medicine_list",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is key
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(task_msgs__msg__CabinetState, medicine_list),  // bytes offset in struct
    NULL,  // default value
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__size_function__CabinetState__medicine_list,  // size() function pointer
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__get_const_function__CabinetState__medicine_list,  // get_const(index) function pointer
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__get_function__CabinetState__medicine_list,  // get(index) function pointer
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__fetch_function__CabinetState__medicine_list,  // fetch(index, &value) function pointer
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__assign_function__CabinetState__medicine_list,  // assign(index, value) function pointer
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__resize_function__CabinetState__medicine_list  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_members = {
  "task_msgs__msg",  // message namespace
  "CabinetState",  // message name
  2,  // number of fields
  sizeof(task_msgs__msg__CabinetState),
  false,  // has_any_key_member_
  task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_member_array,  // message members
  task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_init_function,  // function to initialize message memory (memory has to be allocated)
  task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_type_support_handle = {
  0,
  &task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_members,
  get_message_typesupport_handle_function,
  &task_msgs__msg__CabinetState__get_type_hash,
  &task_msgs__msg__CabinetState__get_type_description,
  &task_msgs__msg__CabinetState__get_type_description_sources,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_task_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, task_msgs, msg, CabinetState)() {
  task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_member_array[1].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, task_msgs, msg, MedicineData)();
  if (!task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_type_support_handle.typesupport_identifier) {
    task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &task_msgs__msg__CabinetState__rosidl_typesupport_introspection_c__CabinetState_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
