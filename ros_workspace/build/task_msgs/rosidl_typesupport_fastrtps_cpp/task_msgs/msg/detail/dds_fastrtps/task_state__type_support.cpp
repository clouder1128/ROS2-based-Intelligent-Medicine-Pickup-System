// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from task_msgs:msg/TaskState.idl
// generated code does not contain a copyright notice
#include "task_msgs/msg/detail/task_state__rosidl_typesupport_fastrtps_cpp.hpp"
#include "task_msgs/msg/detail/task_state__functions.h"
#include "task_msgs/msg/detail/task_state__struct.hpp"

#include <cstddef>
#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/serialization_helpers.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions

namespace task_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{


bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
cdr_serialize(
  const task_msgs::msg::TaskState & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: taskid
  cdr << ros_message.taskid;

  // Member: task_state
  cdr << ros_message.task_state;

  // Member: car_id
  cdr << ros_message.car_id;

  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  task_msgs::msg::TaskState & ros_message)
{
  // Member: taskid
  cdr >> ros_message.taskid;

  // Member: task_state
  cdr >> ros_message.task_state;

  // Member: car_id
  cdr >> ros_message.car_id;

  return true;
}  // NOLINT(readability/fn_size)


size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
get_serialized_size(
  const task_msgs::msg::TaskState & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: taskid
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.taskid.size() + 1);

  // Member: task_state
  {
    size_t item_size = sizeof(ros_message.task_state);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Member: car_id
  {
    size_t item_size = sizeof(ros_message.car_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}


size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
max_serialized_size_TaskState(
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

  // Member: taskid
  {
    size_t array_size = 1;
    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }
  // Member: task_state
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // Member: car_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = task_msgs::msg::TaskState;
    is_plain =
      (
      offsetof(DataType, car_id) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
cdr_serialize_key(
  const task_msgs::msg::TaskState & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: taskid
  cdr << ros_message.taskid;

  // Member: task_state
  cdr << ros_message.task_state;

  // Member: car_id
  cdr << ros_message.car_id;

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
get_serialized_size_key(
  const task_msgs::msg::TaskState & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: taskid
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.taskid.size() + 1);

  // Member: task_state
  {
    size_t item_size = sizeof(ros_message.task_state);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  // Member: car_id
  {
    size_t item_size = sizeof(ros_message.car_id);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
max_serialized_size_key_TaskState(
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

  // Member: taskid
  {
    size_t array_size = 1;
    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  // Member: task_state
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  // Member: car_id
  {
    size_t array_size = 1;
    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = task_msgs::msg::TaskState;
    is_plain =
      (
      offsetof(DataType, car_id) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}


static bool _TaskState__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const task_msgs::msg::TaskState *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _TaskState__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<task_msgs::msg::TaskState *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _TaskState__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const task_msgs::msg::TaskState *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _TaskState__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_TaskState(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _TaskState__callbacks = {
  "task_msgs::msg",
  "TaskState",
  _TaskState__cdr_serialize,
  _TaskState__cdr_deserialize,
  _TaskState__get_serialized_size,
  _TaskState__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _TaskState__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_TaskState__callbacks,
  get_message_typesupport_handle_function,
  &task_msgs__msg__TaskState__get_type_hash,
  &task_msgs__msg__TaskState__get_type_description,
  &task_msgs__msg__TaskState__get_type_description_sources,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace task_msgs

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_task_msgs
const rosidl_message_type_support_t *
get_message_type_support_handle<task_msgs::msg::TaskState>()
{
  return &task_msgs::msg::typesupport_fastrtps_cpp::_TaskState__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, task_msgs, msg, TaskState)() {
  return &task_msgs::msg::typesupport_fastrtps_cpp::_TaskState__handle;
}

#ifdef __cplusplus
}
#endif
