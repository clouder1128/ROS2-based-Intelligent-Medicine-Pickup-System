// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from task_msgs:msg/MedicineData.idl
// generated code does not contain a copyright notice
#include "task_msgs/msg/detail/medicine_data__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <cstddef>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "task_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "task_msgs/msg/detail/medicine_data__struct.h"
#include "task_msgs/msg/detail/medicine_data__functions.h"
#include "fastcdr/Cdr.h"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif


// forward declare type support functions


using _MedicineData__ros_msg_type = task_msgs__msg__MedicineData;


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_serialize_task_msgs__msg__MedicineData(
  const task_msgs__msg__MedicineData * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: row
  {
    cdr << ros_message->row;
  }

  // Field name: column
  {
    cdr << ros_message->column;
  }

  // Field name: count
  {
    cdr << ros_message->count;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_deserialize_task_msgs__msg__MedicineData(
  eprosima::fastcdr::Cdr & cdr,
  task_msgs__msg__MedicineData * ros_message)
{
  // Field name: row
  {
    cdr >> ros_message->row;
  }

  // Field name: column
  {
    cdr >> ros_message->column;
  }

  // Field name: count
  {
    cdr >> ros_message->count;
  }

  return true;
}  // NOLINT(readability/fn_size)


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t get_serialized_size_task_msgs__msg__MedicineData(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _MedicineData__ros_msg_type * ros_message = static_cast<const _MedicineData__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: row
  {
    size_t item_size = sizeof(ros_message->row);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: column
  {
    size_t item_size = sizeof(ros_message->column);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: count
  {
    size_t item_size = sizeof(ros_message->count);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t max_serialized_size_task_msgs__msg__MedicineData(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // Field name: row
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: column
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: count
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }


  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = task_msgs__msg__MedicineData;
    is_plain =
      (
      offsetof(DataType, count) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_serialize_key_task_msgs__msg__MedicineData(
  const task_msgs__msg__MedicineData * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: row
  {
    cdr << ros_message->row;
  }

  // Field name: column
  {
    cdr << ros_message->column;
  }

  // Field name: count
  {
    cdr << ros_message->count;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t get_serialized_size_key_task_msgs__msg__MedicineData(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _MedicineData__ros_msg_type * ros_message = static_cast<const _MedicineData__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;

  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: row
  {
    size_t item_size = sizeof(ros_message->row);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: column
  {
    size_t item_size = sizeof(ros_message->column);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: count
  {
    size_t item_size = sizeof(ros_message->count);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t max_serialized_size_key_task_msgs__msg__MedicineData(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;
  // Field name: row
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: column
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: count
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = task_msgs__msg__MedicineData;
    is_plain =
      (
      offsetof(DataType, count) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}


static bool _MedicineData__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const task_msgs__msg__MedicineData * ros_message = static_cast<const task_msgs__msg__MedicineData *>(untyped_ros_message);
  (void)ros_message;
  return cdr_serialize_task_msgs__msg__MedicineData(ros_message, cdr);
}

static bool _MedicineData__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  task_msgs__msg__MedicineData * ros_message = static_cast<task_msgs__msg__MedicineData *>(untyped_ros_message);
  (void)ros_message;
  return cdr_deserialize_task_msgs__msg__MedicineData(cdr, ros_message);
}

static uint32_t _MedicineData__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_task_msgs__msg__MedicineData(
      untyped_ros_message, 0));
}

static size_t _MedicineData__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_task_msgs__msg__MedicineData(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_MedicineData = {
  "task_msgs::msg",
  "MedicineData",
  _MedicineData__cdr_serialize,
  _MedicineData__cdr_deserialize,
  _MedicineData__get_serialized_size,
  _MedicineData__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _MedicineData__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_MedicineData,
  get_message_typesupport_handle_function,
  &task_msgs__msg__MedicineData__get_type_hash,
  &task_msgs__msg__MedicineData__get_type_description,
  &task_msgs__msg__MedicineData__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, task_msgs, msg, MedicineData)() {
  return &_MedicineData__type_support;
}

#if defined(__cplusplus)
}
#endif
