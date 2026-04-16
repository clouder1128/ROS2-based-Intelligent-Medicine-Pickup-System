// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from task_msgs:msg/CarState.idl
// generated code does not contain a copyright notice

#include "task_msgs/msg/detail/car_state__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_task_msgs
const rosidl_type_hash_t *
task_msgs__msg__CarState__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0xbf, 0x4a, 0x25, 0xb2, 0xbc, 0xfa, 0x8d, 0xfa,
      0xd1, 0x74, 0xf0, 0x82, 0x5f, 0xe4, 0xf5, 0x90,
      0x8e, 0x30, 0xf9, 0x7c, 0xc5, 0x90, 0xd2, 0x00,
      0x44, 0x3b, 0x33, 0xaa, 0xa0, 0x1f, 0x64, 0x78,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types

// Hashes for external referenced types
#ifndef NDEBUG
#endif

static char task_msgs__msg__CarState__TYPE_NAME[] = "task_msgs/msg/CarState";

// Define type names, field names, and default values
static char task_msgs__msg__CarState__FIELD_NAME__car_id[] = "car_id";
static char task_msgs__msg__CarState__FIELD_NAME__x[] = "x";
static char task_msgs__msg__CarState__FIELD_NAME__y[] = "y";
static char task_msgs__msg__CarState__FIELD_NAME__isrunning[] = "isrunning";

static rosidl_runtime_c__type_description__Field task_msgs__msg__CarState__FIELDS[] = {
  {
    {task_msgs__msg__CarState__FIELD_NAME__car_id, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_UINT8,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {task_msgs__msg__CarState__FIELD_NAME__x, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {task_msgs__msg__CarState__FIELD_NAME__y, 1, 1},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {task_msgs__msg__CarState__FIELD_NAME__isrunning, 9, 9},
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
task_msgs__msg__CarState__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {task_msgs__msg__CarState__TYPE_NAME, 22, 22},
      {task_msgs__msg__CarState__FIELDS, 4, 4},
    },
    {NULL, 0, 0},
  };
  if (!constructed) {
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "#CarState.msg\n"
  "uint8 car_id\n"
  "float32 x\n"
  "float32 y\n"
  "uint8 isrunning";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
task_msgs__msg__CarState__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {task_msgs__msg__CarState__TYPE_NAME, 22, 22},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 62, 62},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
task_msgs__msg__CarState__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[1];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 1, 1};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *task_msgs__msg__CarState__get_individual_type_description_source(NULL),
    constructed = true;
  }
  return &source_sequence;
}
