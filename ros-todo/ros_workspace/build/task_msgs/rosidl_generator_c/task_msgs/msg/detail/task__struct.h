// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from task_msgs:msg/Task.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/task.h"


#ifndef TASK_MSGS__MSG__DETAIL__TASK__STRUCT_H_
#define TASK_MSGS__MSG__DETAIL__TASK__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'task_id'
// Member 'type'
#include "rosidl_runtime_c/string.h"
// Member 'cabinets'
#include "task_msgs/msg/detail/cabinet_order__struct.h"

/// Struct defined in msg/Task in the package task_msgs.
/**
  * Task.msg
 */
typedef struct task_msgs__msg__Task
{
  rosidl_runtime_c__String task_id;
  task_msgs__msg__CabinetOrder__Sequence cabinets;
  rosidl_runtime_c__String type;
} task_msgs__msg__Task;

// Struct for a sequence of task_msgs__msg__Task.
typedef struct task_msgs__msg__Task__Sequence
{
  task_msgs__msg__Task * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} task_msgs__msg__Task__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // TASK_MSGS__MSG__DETAIL__TASK__STRUCT_H_
