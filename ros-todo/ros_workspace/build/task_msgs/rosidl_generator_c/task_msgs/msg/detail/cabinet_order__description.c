// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from task_msgs:msg/CabinetOrder.idl
// generated code does not contain a copyright notice

#include "task_msgs/msg/detail/cabinet_order__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_task_msgs
const rosidl_type_hash_t *
task_msgs__msg__CabinetOrder__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x6b, 0xa3, 0x0a, 0x14, 0x9a, 0xf9, 0xcc, 0x4e,
      0x2e, 0xf2, 0x2e, 0xf2, 0xe8, 0xc0, 0xad, 0x3e,
      0x6d, 0x43, 0xf4, 0xc8, 0xfd, 0x32, 0x2f, 0x09,
      0x7b, 0x2c, 0x66, 0xdb, 0x62, 0x40, 0xe4, 0xe6,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "task_msgs/msg/detail/medicine_data__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t task_msgs__msg__MedicineData__EXPECTED_HASH = {1, {
    0xbf, 0xdc, 0x64, 0x0e, 0x05, 0x93, 0xba, 0xfe,
    0xdb, 0x6f, 0x31, 0xbc, 0xbf, 0xfc, 0x68, 0x82,
    0x82, 0x07, 0xdb, 0xc8, 0xe6, 0x70, 0x9c, 0x28,
    0x4f, 0xbd, 0x33, 0x69, 0xae, 0xd4, 0x9a, 0x24,
  }};
#endif

static char task_msgs__msg__CabinetOrder__TYPE_NAME[] = "task_msgs/msg/CabinetOrder";
static char task_msgs__msg__MedicineData__TYPE_NAME[] = "task_msgs/msg/MedicineData";

// Define type names, field names, and default values
static char task_msgs__msg__CabinetOrder__FIELD_NAME__cabinet_id[] = "cabinet_id";
static char task_msgs__msg__CabinetOrder__FIELD_NAME__medicine_list[] = "medicine_list";

static rosidl_runtime_c__type_description__Field task_msgs__msg__CabinetOrder__FIELDS[] = {
  {
    {task_msgs__msg__CabinetOrder__FIELD_NAME__cabinet_id, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_STRING,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {task_msgs__msg__CabinetOrder__FIELD_NAME__medicine_list, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE_UNBOUNDED_SEQUENCE,
      0,
      0,
      {task_msgs__msg__MedicineData__TYPE_NAME, 26, 26},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription task_msgs__msg__CabinetOrder__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {task_msgs__msg__MedicineData__TYPE_NAME, 26, 26},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
task_msgs__msg__CabinetOrder__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {task_msgs__msg__CabinetOrder__TYPE_NAME, 26, 26},
      {task_msgs__msg__CabinetOrder__FIELDS, 2, 2},
    },
    {task_msgs__msg__CabinetOrder__REFERENCED_TYPE_DESCRIPTIONS, 1, 1},
  };
  if (!constructed) {
    assert(0 == memcmp(&task_msgs__msg__MedicineData__EXPECTED_HASH, task_msgs__msg__MedicineData__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = task_msgs__msg__MedicineData__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "# CabinetOrder.msg\n"
  "string cabinet_id\n"
  "MedicineData[] medicine_list";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
task_msgs__msg__CabinetOrder__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {task_msgs__msg__CabinetOrder__TYPE_NAME, 26, 26},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 66, 66},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
task_msgs__msg__CabinetOrder__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[2];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 2, 2};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *task_msgs__msg__CabinetOrder__get_individual_type_description_source(NULL),
    sources[1] = *task_msgs__msg__MedicineData__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
