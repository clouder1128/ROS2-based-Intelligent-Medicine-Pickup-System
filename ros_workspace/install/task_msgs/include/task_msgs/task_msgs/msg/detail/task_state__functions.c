// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from task_msgs:msg/TaskState.idl
// generated code does not contain a copyright notice
#include "task_msgs/msg/detail/task_state__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `taskid`
#include "rosidl_runtime_c/string_functions.h"

bool
task_msgs__msg__TaskState__init(task_msgs__msg__TaskState * msg)
{
  if (!msg) {
    return false;
  }
  // taskid
  if (!rosidl_runtime_c__String__init(&msg->taskid)) {
    task_msgs__msg__TaskState__fini(msg);
    return false;
  }
  // task_state
  // car_id
  return true;
}

void
task_msgs__msg__TaskState__fini(task_msgs__msg__TaskState * msg)
{
  if (!msg) {
    return;
  }
  // taskid
  rosidl_runtime_c__String__fini(&msg->taskid);
  // task_state
  // car_id
}

bool
task_msgs__msg__TaskState__are_equal(const task_msgs__msg__TaskState * lhs, const task_msgs__msg__TaskState * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // taskid
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->taskid), &(rhs->taskid)))
  {
    return false;
  }
  // task_state
  if (lhs->task_state != rhs->task_state) {
    return false;
  }
  // car_id
  if (lhs->car_id != rhs->car_id) {
    return false;
  }
  return true;
}

bool
task_msgs__msg__TaskState__copy(
  const task_msgs__msg__TaskState * input,
  task_msgs__msg__TaskState * output)
{
  if (!input || !output) {
    return false;
  }
  // taskid
  if (!rosidl_runtime_c__String__copy(
      &(input->taskid), &(output->taskid)))
  {
    return false;
  }
  // task_state
  output->task_state = input->task_state;
  // car_id
  output->car_id = input->car_id;
  return true;
}

task_msgs__msg__TaskState *
task_msgs__msg__TaskState__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__TaskState * msg = (task_msgs__msg__TaskState *)allocator.allocate(sizeof(task_msgs__msg__TaskState), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(task_msgs__msg__TaskState));
  bool success = task_msgs__msg__TaskState__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
task_msgs__msg__TaskState__destroy(task_msgs__msg__TaskState * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    task_msgs__msg__TaskState__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
task_msgs__msg__TaskState__Sequence__init(task_msgs__msg__TaskState__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__TaskState * data = NULL;

  if (size) {
    data = (task_msgs__msg__TaskState *)allocator.zero_allocate(size, sizeof(task_msgs__msg__TaskState), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = task_msgs__msg__TaskState__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        task_msgs__msg__TaskState__fini(&data[i - 1]);
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
task_msgs__msg__TaskState__Sequence__fini(task_msgs__msg__TaskState__Sequence * array)
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
      task_msgs__msg__TaskState__fini(&array->data[i]);
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

task_msgs__msg__TaskState__Sequence *
task_msgs__msg__TaskState__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  task_msgs__msg__TaskState__Sequence * array = (task_msgs__msg__TaskState__Sequence *)allocator.allocate(sizeof(task_msgs__msg__TaskState__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = task_msgs__msg__TaskState__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
task_msgs__msg__TaskState__Sequence__destroy(task_msgs__msg__TaskState__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    task_msgs__msg__TaskState__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
task_msgs__msg__TaskState__Sequence__are_equal(const task_msgs__msg__TaskState__Sequence * lhs, const task_msgs__msg__TaskState__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!task_msgs__msg__TaskState__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
task_msgs__msg__TaskState__Sequence__copy(
  const task_msgs__msg__TaskState__Sequence * input,
  task_msgs__msg__TaskState__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(task_msgs__msg__TaskState);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    task_msgs__msg__TaskState * data =
      (task_msgs__msg__TaskState *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!task_msgs__msg__TaskState__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          task_msgs__msg__TaskState__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!task_msgs__msg__TaskState__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
