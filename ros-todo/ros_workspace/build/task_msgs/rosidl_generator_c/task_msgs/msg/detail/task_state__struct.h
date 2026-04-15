// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from task_msgs:msg/TaskState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/task_state.h"


#ifndef TASK_MSGS__MSG__DETAIL__TASK_STATE__STRUCT_H_
#define TASK_MSGS__MSG__DETAIL__TASK_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'taskid'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/TaskState in the package task_msgs.
/**
  * TaskState.msg
 */
typedef struct task_msgs__msg__TaskState
{
  rosidl_runtime_c__String taskid;
  int32_t task_state;
  int32_t car_id;
} task_msgs__msg__TaskState;

// Struct for a sequence of task_msgs__msg__TaskState.
typedef struct task_msgs__msg__TaskState__Sequence
{
  task_msgs__msg__TaskState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} task_msgs__msg__TaskState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // TASK_MSGS__MSG__DETAIL__TASK_STATE__STRUCT_H_
