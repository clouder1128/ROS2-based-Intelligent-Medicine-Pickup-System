// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from task_msgs:msg/CabinetState.idl
// generated code does not contain a copyright notice
#include "task_msgs/msg/detail/cabinet_state__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <cstddef>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "task_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "task_msgs/msg/detail/cabinet_state__struct.h"
#include "task_msgs/msg/detail/cabinet_state__functions.h"
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

#include "task_msgs/msg/detail/medicine_data__functions.h"  // medicine_list

// forward declare type support functions

bool cdr_serialize_task_msgs__msg__MedicineData(
  const task_msgs__msg__MedicineData * ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool cdr_deserialize_task_msgs__msg__MedicineData(
  eprosima::fastcdr::Cdr & cdr,
  task_msgs__msg__MedicineData * ros_message);

size_t get_serialized_size_task_msgs__msg__MedicineData(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_task_msgs__msg__MedicineData(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

bool cdr_serialize_key_task_msgs__msg__MedicineData(
  const task_msgs__msg__MedicineData * ros_message,
  eprosima::fastcdr::Cdr & cdr);

size_t get_serialized_size_key_task_msgs__msg__MedicineData(
  const void * untyped_ros_message,
  size_t current_alignment);

size_t max_serialized_size_key_task_msgs__msg__MedicineData(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, task_msgs, msg, MedicineData)();


using _CabinetState__ros_msg_type = task_msgs__msg__CabinetState;


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_serialize_task_msgs__msg__CabinetState(
  const task_msgs__msg__CabinetState * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: cabinet_id
  {
    cdr << ros_message->cabinet_id;
  }

  // Field name: medicine_list
  {
    size_t size = ros_message->medicine_list.size;
    auto array_ptr = ros_message->medicine_list.data;
    cdr << static_cast<uint32_t>(size);
    for (size_t i = 0; i < size; ++i) {
      cdr_serialize_task_msgs__msg__MedicineData(
        &array_ptr[i], cdr);
    }
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_deserialize_task_msgs__msg__CabinetState(
  eprosima::fastcdr::Cdr & cdr,
  task_msgs__msg__CabinetState * ros_message)
{
  // Field name: cabinet_id
  {
    cdr >> ros_message->cabinet_id;
  }

  // Field name: medicine_list
  {
    uint32_t cdrSize;
    cdr >> cdrSize;
    size_t size = static_cast<size_t>(cdrSize);

    // Check there are at least 'size' remaining bytes in the CDR stream before resizing
    auto old_state = cdr.get_state();
    bool correct_size = cdr.jump(size);
    cdr.set_state(old_state);
    if (!correct_size) {
      fprintf(stderr, "sequence size exceeds remaining buffer\n");
      return false;
    }

    if (ros_message->medicine_list.data) {
      task_msgs__msg__MedicineData__Sequence__fini(&ros_message->medicine_list);
    }
    if (!task_msgs__msg__MedicineData__Sequence__init(&ros_message->medicine_list, size)) {
      fprintf(stderr, "failed to create array for field 'medicine_list'");
      return false;
    }
    auto array_ptr = ros_message->medicine_list.data;
    for (size_t i = 0; i < size; ++i) {
      cdr_deserialize_task_msgs__msg__MedicineData(cdr, &array_ptr[i]);
    }
  }

  return true;
}  // NOLINT(readability/fn_size)


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t get_serialized_size_task_msgs__msg__CabinetState(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _CabinetState__ros_msg_type * ros_message = static_cast<const _CabinetState__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: cabinet_id
  {
    size_t item_size = sizeof(ros_message->cabinet_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: medicine_list
  {
    size_t array_size = ros_message->medicine_list.size;
    auto array_ptr = ros_message->medicine_list.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += get_serialized_size_task_msgs__msg__MedicineData(
        &array_ptr[index], current_alignment);
    }
  }

  return current_alignment - initial_alignment;
}


ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t max_serialized_size_task_msgs__msg__CabinetState(
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

  // Field name: cabinet_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: medicine_list
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_task_msgs__msg__MedicineData(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }


  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = task_msgs__msg__CabinetState;
    is_plain =
      (
      offsetof(DataType, medicine_list) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
bool cdr_serialize_key_task_msgs__msg__CabinetState(
  const task_msgs__msg__CabinetState * ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Field name: cabinet_id
  {
    cdr << ros_message->cabinet_id;
  }

  // Field name: medicine_list
  {
    size_t size = ros_message->medicine_list.size;
    auto array_ptr = ros_message->medicine_list.data;
    cdr << static_cast<uint32_t>(size);
    for (size_t i = 0; i < size; ++i) {
      cdr_serialize_key_task_msgs__msg__MedicineData(
        &array_ptr[i], cdr);
    }
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t get_serialized_size_key_task_msgs__msg__CabinetState(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _CabinetState__ros_msg_type * ros_message = static_cast<const _CabinetState__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;

  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Field name: cabinet_id
  {
    size_t item_size = sizeof(ros_message->cabinet_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Field name: medicine_list
  {
    size_t array_size = ros_message->medicine_list.size;
    auto array_ptr = ros_message->medicine_list.data;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += get_serialized_size_key_task_msgs__msg__MedicineData(
        &array_ptr[index], current_alignment);
    }
  }

  return current_alignment - initial_alignment;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_task_msgs
size_t max_serialized_size_key_task_msgs__msg__CabinetState(
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
  // Field name: cabinet_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Field name: medicine_list
  {
    size_t array_size = 0;
    full_bounded = false;
    is_plain = false;
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    last_member_size = 0;
    for (size_t index = 0; index < array_size; ++index) {
      bool inner_full_bounded;
      bool inner_is_plain;
      size_t inner_size;
      inner_size =
        max_serialized_size_key_task_msgs__msg__MedicineData(
        inner_full_bounded, inner_is_plain, current_alignment);
      last_member_size += inner_size;
      current_alignment += inner_size;
      full_bounded &= inner_full_bounded;
      is_plain &= inner_is_plain;
    }
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = task_msgs__msg__CabinetState;
    is_plain =
      (
      offsetof(DataType, medicine_list) +
      last_member_size
      ) == ret_val;
  }
  return ret_val;
}


static bool _CabinetState__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const task_msgs__msg__CabinetState * ros_message = static_cast<const task_msgs__msg__CabinetState *>(untyped_ros_message);
  (void)ros_message;
  return cdr_serialize_task_msgs__msg__CabinetState(ros_message, cdr);
}

static bool _CabinetState__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  task_msgs__msg__CabinetState * ros_message = static_cast<task_msgs__msg__CabinetState *>(untyped_ros_message);
  (void)ros_message;
  return cdr_deserialize_task_msgs__msg__CabinetState(cdr, ros_message);
}

static uint32_t _CabinetState__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_task_msgs__msg__CabinetState(
      untyped_ros_message, 0));
}

static size_t _CabinetState__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_task_msgs__msg__CabinetState(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_CabinetState = {
  "task_msgs::msg",
  "CabinetState",
  _CabinetState__cdr_serialize,
  _CabinetState__cdr_deserialize,
  _CabinetState__get_serialized_size,
  _CabinetState__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _CabinetState__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_CabinetState,
  get_message_typesupport_handle_function,
  &task_msgs__msg__CabinetState__get_type_hash,
  &task_msgs__msg__CabinetState__get_type_description,
  &task_msgs__msg__CabinetState__get_type_description_sources,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, task_msgs, msg, CabinetState)() {
  return &_CabinetState__type_support;
}

#if defined(__cplusplus)
}
#endif
