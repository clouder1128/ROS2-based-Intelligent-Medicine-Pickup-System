// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from task_msgs:msg/TaskState.idl
// generated code does not contain a copyright notice

#include "task_msgs/msg/detail/task_state__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_task_msgs
const rosidl_type_hash_t *
task_msgs__msg__TaskState__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x31, 0xe0, 0x1b, 0x53, 0x91, 0xf1, 0x58, 0x9e,
      0xb9, 0x59, 0x02, 0x25, 0xbd, 0x66, 0x52, 0x1c,
      0xb5, 0xa7, 0x7d, 0xa8, 0x07, 0xfa, 0x86, 0x30,
      0xd5, 0xe1, 0x59, 0x0e, 0xb7, 0xa9, 0xaa, 0xab,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char task_msgs__msg__TaskState__TYPE_NAME[] = "task_msgs/msg/TaskState";

// Define type names, field names, and default values
static char task_msgs__msg__TaskState__FIELD_NAME__taskid[] = "taskid";
static char task_msgs__msg__TaskState__FIELD_NAME__task_state[] = "task_state";
static char task_msgs__msg__TaskState__FIELD_NAME__car_id[] = "car_id";

static rosidl_runtime_c__type_description__Field task_msgs__msg__TaskState__FIELDS[] = {
  {
    {task_msgs__msg__TaskState__FIELD_NAME__taskid, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {task_msgs__msg__TaskState__FIELD_NAME__task_state, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {task_msgs__msg__TaskState__FIELD_NAME__car_id, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_INT32,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
task_msgs__msg__TaskState__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {task_msgs__msg__TaskState__TYPE_NAME, 23, 23},
      {task_msgs__msg__TaskState__FIELDS, 3, 3},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "#TaskState.msg\n"
  "string taskid\n"
  "int32 task_state\n"
  "int32 car_id";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
task_msgs__msg__TaskState__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {task_msgs__msg__TaskState__TYPE_NAME, 23, 23},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 58, 58},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
task_msgs__msg__TaskState__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *task_msgs__msg__TaskState__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
