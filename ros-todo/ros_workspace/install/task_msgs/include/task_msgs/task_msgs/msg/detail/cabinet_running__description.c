// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from task_msgs:msg/CabinetRunning.idl
// generated code does not contain a copyright notice

#include "task_msgs/msg/detail/cabinet_running__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_task_msgs
const rosidl_type_hash_t *
task_msgs__msg__CabinetRunning__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x04, 0xcc, 0x66, 0xc1, 0x1a, 0x39, 0x21, 0xcd,
      0x87, 0x09, 0x63, 0x77, 0x52, 0xa3, 0x82, 0x94,
      0x4c, 0x3a, 0xeb, 0x31, 0xb6, 0xa4, 0xac, 0x99,
      0x22, 0x88, 0x7b, 0x29, 0x29, 0xb9, 0x90, 0x99,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char task_msgs__msg__CabinetRunning__TYPE_NAME[] = "task_msgs/msg/CabinetRunning";

// Define type names, field names, and default values
static char task_msgs__msg__CabinetRunning__FIELD_NAME__cabinet_id[] = "cabinet_id";
static char task_msgs__msg__CabinetRunning__FIELD_NAME__isrunning[] = "isrunning";

static rosidl_runtime_c__type_description__Field task_msgs__msg__CabinetRunning__FIELDS[] = {
  {
    {task_msgs__msg__CabinetRunning__FIELD_NAME__cabinet_id, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {task_msgs__msg__CabinetRunning__FIELD_NAME__isrunning, 9, 9},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
task_msgs__msg__CabinetRunning__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {task_msgs__msg__CabinetRunning__TYPE_NAME, 28, 28},
      {task_msgs__msg__CabinetRunning__FIELDS, 2, 2},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "#CabinetRunning.msg\n"
  "uint8 cabinet_id\n"
  "uint8 isrunning";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
task_msgs__msg__CabinetRunning__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {task_msgs__msg__CabinetRunning__TYPE_NAME, 28, 28},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 52, 52},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
task_msgs__msg__CabinetRunning__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *task_msgs__msg__CabinetRunning__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
