// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from task_msgs:msg/CabinetState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_state.h"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_STATE__STRUCT_H_
#define TASK_MSGS__MSG__DETAIL__CABINET_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'medicine_list'
#include "task_msgs/msg/detail/medicine_data__struct.h"

/// Struct defined in msg/CabinetState in the package task_msgs.
/**
  * CabinetState.msg
 */
typedef struct task_msgs__msg__CabinetState
{
  uint8_t cabinet_id;
  task_msgs__msg__MedicineData__Sequence medicine_list;
} task_msgs__msg__CabinetState;

// Struct for a sequence of task_msgs__msg__CabinetState.
typedef struct task_msgs__msg__CabinetState__Sequence
{
  task_msgs__msg__CabinetState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} task_msgs__msg__CabinetState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_STATE__STRUCT_H_
