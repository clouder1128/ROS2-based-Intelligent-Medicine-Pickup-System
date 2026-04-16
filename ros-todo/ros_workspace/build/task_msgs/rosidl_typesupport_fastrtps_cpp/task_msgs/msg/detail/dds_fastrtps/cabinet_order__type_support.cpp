// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from task_msgs:msg/CabinetOrder.idl
// generated code does not contain a copyright notice
#include "task_msgs/msg/detail/cabinet_order__rosidl_typesupport_fastrtps_cpp.hpp"
#include "task_msgs/msg/detail/cabinet_order__functions.h"
#include "task_msgs/msg/detail/cabinet_order__struct.hpp"

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
bool cdr_serialize(
  const task_msgs::msg::MedicineData &,
  eprosima::fastcdr::Cdr &);
bool cdr_deserialize(
  eprosima::fastcdr::Cdr &,
  task_msgs::msg::MedicineData &);
size_t get_serialized_size(
  const task_msgs::msg::MedicineData &,
  size_t current_alignment);
size_t
max_serialized_size_MedicineData(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);
bool cdr_serialize_key(
  const task_msgs::msg::MedicineData &,
  eprosima::fastcdr::Cdr &);
size_t get_serialized_size_key(
  const task_msgs::msg::MedicineData &,
  size_t current_alignment);
size_t
max_serialized_size_key_MedicineData(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);
}  // namespace typesupport_fastrtps_cpp
}  // namespace msg
}  // namespace task_msgs


namespace task_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{


bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
cdr_serialize(
  const task_msgs::msg::CabinetOrder & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: cabinet_id
  cdr << ros_message.cabinet_id;

  // Member: medicine_list
  {
    size_t size = ros_message.medicine_list.size();
    cdr << static_cast<uint32_t>(size);
    for (size_t i = 0; i < size; i++) {
      task_msgs::msg::typesupport_fastrtps_cpp::cdr_serialize(
        ros_message.medicine_list[i],
        cdr);
    }
  }

  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  task_msgs::msg::CabinetOrder & ros_message)
{
  // Member: cabinet_id
  cdr >> ros_message.cabinet_id;

  // Member: medicine_list
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

    ros_message.medicine_list.resize(size);
    for (size_t i = 0; i < size; i++) {
      task_msgs::msg::typesupport_fastrtps_cpp::cdr_deserialize(
        cdr, ros_message.medicine_list[i]);
    }
  }

  return true;
}  // NOLINT(readability/fn_size)


size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
get_serialized_size(
  const task_msgs::msg::CabinetOrder & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: cabinet_id
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.cabinet_id.size() + 1);

  // Member: medicine_list
  {
    size_t array_size = ros_message.medicine_list.size();
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment +=
        task_msgs::msg::typesupport_fastrtps_cpp::get_serialized_size(
        ros_message.medicine_list[index], current_alignment);
    }
  }

  return current_alignment - initial_alignment;
}


size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
max_serialized_size_CabinetOrder(
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

  // Member: cabinet_id
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
  // Member: medicine_list
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
      size_t inner_size =
        task_msgs::msg::typesupport_fastrtps_cpp::max_serialized_size_MedicineData(
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
    using DataType = task_msgs::msg::CabinetOrder;
    is_plain =
      (
      offsetof(DataType, medicine_list) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
cdr_serialize_key(
  const task_msgs::msg::CabinetOrder & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: cabinet_id
  cdr << ros_message.cabinet_id;

  // Member: medicine_list
  {
    size_t size = ros_message.medicine_list.size();
    cdr << static_cast<uint32_t>(size);
    for (size_t i = 0; i < size; i++) {
      task_msgs::msg::typesupport_fastrtps_cpp::cdr_serialize_key(
        ros_message.medicine_list[i],
        cdr);
    }
  }

  return true;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
get_serialized_size_key(
  const task_msgs::msg::CabinetOrder & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: cabinet_id
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.cabinet_id.size() + 1);

  // Member: medicine_list
  {
    size_t array_size = ros_message.medicine_list.size();
    current_alignment += padding +
      eprosima::fastcdr::Cdr::alignment(current_alignment, padding);
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment +=
        task_msgs::msg::typesupport_fastrtps_cpp::get_serialized_size_key(
        ros_message.medicine_list[index], current_alignment);
    }
  }

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_task_msgs
max_serialized_size_key_CabinetOrder(
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

  // Member: cabinet_id
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

  // Member: medicine_list
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
      size_t inner_size =
        task_msgs::msg::typesupport_fastrtps_cpp::max_serialized_size_key_MedicineData(
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
    using DataType = task_msgs::msg::CabinetOrder;
    is_plain =
      (
      offsetof(DataType, medicine_list) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}


static bool _CabinetOrder__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const task_msgs::msg::CabinetOrder *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _CabinetOrder__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<task_msgs::msg::CabinetOrder *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _CabinetOrder__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const task_msgs::msg::CabinetOrder *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _CabinetOrder__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_CabinetOrder(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _CabinetOrder__callbacks = {
  "task_msgs::msg",
  "CabinetOrder",
  _CabinetOrder__cdr_serialize,
  _CabinetOrder__cdr_deserialize,
  _CabinetOrder__get_serialized_size,
  _CabinetOrder__max_serialized_size,
  nullptr
};

static rosidl_message_type_support_t _CabinetOrder__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_CabinetOrder__callbacks,
  get_message_typesupport_handle_function,
  &task_msgs__msg__CabinetOrder__get_type_hash,
  &task_msgs__msg__CabinetOrder__get_type_description,
  &task_msgs__msg__CabinetOrder__get_type_description_sources,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace task_msgs

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_task_msgs
const rosidl_message_type_support_t *
get_message_type_support_handle<task_msgs::msg::CabinetOrder>()
{
  return &task_msgs::msg::typesupport_fastrtps_cpp::_CabinetOrder__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, task_msgs, msg, CabinetOrder)() {
  return &task_msgs::msg::typesupport_fastrtps_cpp::_CabinetOrder__handle;
}

#ifdef __cplusplus
}
#endif
