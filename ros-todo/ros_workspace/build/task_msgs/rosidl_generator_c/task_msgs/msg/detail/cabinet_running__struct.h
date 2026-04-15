// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from task_msgs:msg/CabinetRunning.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/cabinet_running.h"


#ifndef TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__STRUCT_H_
#define TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Struct defined in msg/CabinetRunning in the package task_msgs.
/**
  * CabinetRunning.msg
 */
typedef struct task_msgs__msg__CabinetRunning
{
  uint8_t cabinet_id;
  uint8_t isrunning;
} task_msgs__msg__CabinetRunning;

// Struct for a sequence of task_msgs__msg__CabinetRunning.
typedef struct task_msgs__msg__CabinetRunning__Sequence
{
  task_msgs__msg__CabinetRunning * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} task_msgs__msg__CabinetRunning__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // TASK_MSGS__MSG__DETAIL__CABINET_RUNNING__STRUCT_H_
