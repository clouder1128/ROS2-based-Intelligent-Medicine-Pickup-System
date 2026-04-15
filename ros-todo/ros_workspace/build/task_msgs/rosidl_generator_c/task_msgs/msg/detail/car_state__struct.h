// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from task_msgs:msg/CarState.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/car_state.h"


#ifndef TASK_MSGS__MSG__DETAIL__CAR_STATE__STRUCT_H_
#define TASK_MSGS__MSG__DETAIL__CAR_STATE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Struct defined in msg/CarState in the package task_msgs.
/**
  * CarState.msg
 */
typedef struct task_msgs__msg__CarState
{
  uint8_t car_id;
  float x;
  float y;
  uint8_t isrunning;
} task_msgs__msg__CarState;

// Struct for a sequence of task_msgs__msg__CarState.
typedef struct task_msgs__msg__CarState__Sequence
{
  task_msgs__msg__CarState * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} task_msgs__msg__CarState__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // TASK_MSGS__MSG__DETAIL__CAR_STATE__STRUCT_H_
