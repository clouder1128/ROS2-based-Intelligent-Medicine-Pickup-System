// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from task_msgs:msg/CabinetState.idl
// generated code does not contain a copyright notice
#include "task_msgs/msg/detail/cabinet_state__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `medicine_list`
#include "task_msgs/msg/detail/medicine_data__functions.h"

bool
task_msgs__msg__CabinetState__init(task_msgs__msg__CabinetState * msg)
{
  if (!msg) {
    return false;
  }
  // cabinet_id
  // medicine_list
  if (!task_msgs__msg__MedicineData__Sequence__init(&msg->medicine_list, 0)) {
    task_msgs__msg__CabinetState__fini(msg);
    return false;
  }
  return true;
}

void
task_msgs__msg__CabinetState__fini(task_msgs__msg__CabinetState * msg)
{
  if (!msg) {
    return;
  }
  // cabinet_id
  // medicine_list
  task_msgs__msg__MedicineData__Sequence__fini(&msg->medicine_list);
}

bool
task_msgs__msg__CabinetState__are_equal(const task_msgs__msg__CabinetState * lhs, const task_msgs__msg__CabinetState * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // cabinet_id
  if (lhs->cabinet_id != rhs->cabinet_id) {
    return false;
  }
  // medicine_list
  if (!task_msgs__msg__MedicineData__Sequence__are_equal(
      &(lhs->medicine_list), &(rhs->medicine_list)))
  {
    return false;
  }
  return true;
}

bool
task_msgs__msg__CabinetState__copy(
  const task_msgs__msg__CabinetState * input,
  task_msgs__msg__CabinetState * output)
{
  if (!input || !output) {
    return false;
  }
  // cabinet_id
  output->cabinet_id = input->cabinet_id;
  // medicine_list
  if (!task_msgs__msg__MedicineData__Sequence__copy(
      &(input->medicine_list), &(output->medicine_list)))
  {
    return false;
  }
  return true;
}

task_msgs__msg__CabinetState *
task_msgs__msg__CabinetState__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__CabinetState * msg = (task_msgs__msg__CabinetState *)allocator.allocate(sizeof(task_msgs__msg__CabinetState), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(task_msgs__msg__CabinetState));
  bool success = task_msgs__msg__CabinetState__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
task_msgs__msg__CabinetState__destroy(task_msgs__msg__CabinetState * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    task_msgs__msg__CabinetState__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
task_msgs__msg__CabinetState__Sequence__init(task_msgs__msg__CabinetState__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__CabinetState * data = NULL;

  if (size) {
    data = (task_msgs__msg__CabinetState *)allocator.zero_allocate(size, sizeof(task_msgs__msg__CabinetState), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = task_msgs__msg__CabinetState__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        task_msgs__msg__CabinetState__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
task_msgs__msg__CabinetState__Sequence__fini(task_msgs__msg__CabinetState__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      task_msgs__msg__CabinetState__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

task_msgs__msg__CabinetState__Sequence *
task_msgs__msg__CabinetState__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__CabinetState__Sequence * array = (task_msgs__msg__CabinetState__Sequence *)allocator.allocate(sizeof(task_msgs__msg__CabinetState__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = task_msgs__msg__CabinetState__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
task_msgs__msg__CabinetState__Sequence__destroy(task_msgs__msg__CabinetState__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    task_msgs__msg__CabinetState__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
task_msgs__msg__CabinetState__Sequence__are_equal(const task_msgs__msg__CabinetState__Sequence * lhs, const task_msgs__msg__CabinetState__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!task_msgs__msg__CabinetState__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
task_msgs__msg__CabinetState__Sequence__copy(
  const task_msgs__msg__CabinetState__Sequence * input,
  task_msgs__msg__CabinetState__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(task_msgs__msg__CabinetState);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    task_msgs__msg__CabinetState * data =
      (task_msgs__msg__CabinetState *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!task_msgs__msg__CabinetState__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          task_msgs__msg__CabinetState__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!task_msgs__msg__CabinetState__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
