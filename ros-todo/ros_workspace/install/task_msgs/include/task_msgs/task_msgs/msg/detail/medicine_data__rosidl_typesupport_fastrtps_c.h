// generated from rosidl_typesupport_fastrtps_c/resource/idl__rosidl_typesupport_fastrtps_c.h.em
// with input from task_msgs:msg/MedicineData.idl
// generated code does not contain a copyright notice
#ifndef TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
#define TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_


#include <stddef.h>
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "task_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "task_msgs/msg/detail/medicine_data__struct.h"
#include "fastcdr/Cdr.h"

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_serialize_task_msgs__msg__MedicineData(
  const task_msgs__msg__MedicineData * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_deserialize_task_msgs__msg__MedicineData(
  eprosima::fastcdr::Cdr &,
  task_msgs__msg__MedicineData * ros_message);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t get_serialized_size_task_msgs__msg__MedicineData(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t max_serialized_size_task_msgs__msg__MedicineData(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_serialize_key_task_msgs__msg__MedicineData(
  const task_msgs__msg__MedicineData * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t get_serialized_size_key_task_msgs__msg__MedicineData(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t max_serialized_size_key_task_msgs__msg__MedicineData(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, task_msgs, msg, MedicineData)();

#ifdef __cplusplus
}
#endif

#endif  // TASK_MSGS__MSG__DETAIL__MEDICINE_DATA__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
