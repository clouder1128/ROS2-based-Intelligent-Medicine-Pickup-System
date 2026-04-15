// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from task_msgs:msg/MedicineData.idl
// generated code does not contain a copyright notice
#include "task_msgs/msg/detail/medicine_data__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
task_msgs__msg__MedicineData__init(task_msgs__msg__MedicineData * msg)
{
  if (!msg) {
    return false;
  }
  // row
  // column
  // count
  return true;
}

void
task_msgs__msg__MedicineData__fini(task_msgs__msg__MedicineData * msg)
{
  if (!msg) {
    return;
  }
  // row
  // column
  // count
}

bool
task_msgs__msg__MedicineData__are_equal(const task_msgs__msg__MedicineData * lhs, const task_msgs__msg__MedicineData * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // row
  if (lhs->row != rhs->row) {
    return false;
  }
  // column
  if (lhs->column != rhs->column) {
    return false;
  }
  // count
  if (lhs->count != rhs->count) {
    return false;
  }
  return true;
}

bool
task_msgs__msg__MedicineData__copy(
  const task_msgs__msg__MedicineData * input,
  task_msgs__msg__MedicineData * output)
{
  if (!input || !output) {
    return false;
  }
  // row
  output->row = input->row;
  // column
  output->column = input->column;
  // count
  output->count = input->count;
  return true;
}

task_msgs__msg__MedicineData *
task_msgs__msg__MedicineData__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__MedicineData * msg = (task_msgs__msg__MedicineData *)allocator.allocate(sizeof(task_msgs__msg__MedicineData), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(task_msgs__msg__MedicineData));
  bool success = task_msgs__msg__MedicineData__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
task_msgs__msg__MedicineData__destroy(task_msgs__msg__MedicineData * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    task_msgs__msg__MedicineData__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
task_msgs__msg__MedicineData__Sequence__init(task_msgs__msg__MedicineData__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__MedicineData * data = NULL;

  if (size) {
    data = (task_msgs__msg__MedicineData *)allocator.zero_allocate(size, sizeof(task_msgs__msg__MedicineData), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = task_msgs__msg__MedicineData__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        task_msgs__msg__MedicineData__fini(&data[i - 1]);
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
task_msgs__msg__MedicineData__Sequence__fini(task_msgs__msg__MedicineData__Sequence * array)
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
      task_msgs__msg__MedicineData__fini(&array->data[i]);
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

task_msgs__msg__MedicineData__Sequence *
task_msgs__msg__MedicineData__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__MedicineData__Sequence * array = (task_msgs__msg__MedicineData__Sequence *)allocator.allocate(sizeof(task_msgs__msg__MedicineData__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = task_msgs__msg__MedicineData__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
task_msgs__msg__MedicineData__Sequence__destroy(task_msgs__msg__MedicineData__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    task_msgs__msg__MedicineData__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
task_msgs__msg__MedicineData__Sequence__are_equal(const task_msgs__msg__MedicineData__Sequence * lhs, const task_msgs__msg__MedicineData__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!task_msgs__msg__MedicineData__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
task_msgs__msg__MedicineData__Sequence__copy(
  const task_msgs__msg__MedicineData__Sequence * input,
  task_msgs__msg__MedicineData__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(task_msgs__msg__MedicineData);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    task_msgs__msg__MedicineData * data =
      (task_msgs__msg__MedicineData *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!task_msgs__msg__MedicineData__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          task_msgs__msg__MedicineData__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!task_msgs__msg__MedicineData__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
