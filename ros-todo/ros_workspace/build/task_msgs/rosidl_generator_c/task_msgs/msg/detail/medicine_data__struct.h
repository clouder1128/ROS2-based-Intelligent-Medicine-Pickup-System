// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from task_msgs:msg/MedicineData.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "task_msgs/msg/medicine_data.h"


#ifndef TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__STRUCT_H_
#define TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

/// Struct defined in msg/MedicineData in the package task_msgs.
/**
  * MedicineData.msg
 */
typedef struct task_msgs__msg__MedicineData
{
  uint8_t row;
  uint8_t column;
  uint8_t count;
} task_msgs__msg__MedicineData;

// Struct for a sequence of task_msgs__msg__MedicineData.
typedef struct task_msgs__msg__MedicineData__Sequence
{
  task_msgs__msg__MedicineData * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} task_msgs__msg__MedicineData__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__STRUCT_H_
