// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from task_msgs:msg/CabinetState.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "task_msgs/msg/detail/cabinet_state__struct.h"
#include "task_msgs/msg/detail/cabinet_state__functions.h"

#include "rosidl_runtime_c/primitives_sequence.h"
#include "rosidl_runtime_c/primitives_sequence_functions.h"

// Nested array functions includes
#include "task_msgs/msg/detail/medicine_data__functions.h"
// end nested array functions include
bool task_msgs__msg__medicine_data__convert_from_py(PyObject * _pymsg, void * _ros_message);
PyObject * task_msgs__msg__medicine_data__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool task_msgs__msg__cabinet_state__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[42];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("task_msgs.msg._cabinet_state.CabinetState", full_classname_dest, 41) == 0);
  }
  task_msgs__msg__CabinetState * ros_message = _ros_message;
  {  // cabinet_id
    PyObject * field = PyObject_GetAttrString(_pymsg, "cabinet_id");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->cabinet_id = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // medicine_list
    PyObject * field = PyObject_GetAttrString(_pymsg, "medicine_list");
    if (!field) {
      return false;
    }
    PyObject * seq_field = PySequence_Fast(field, "expected a sequence in 'medicine_list'");
    if (!seq_field) {
      Py_DECREF(field);
      return false;
    }
    Py_ssize_t size = PySequence_Size(field);
    if (-1 == size) {
      Py_DECREF(seq_field);
      Py_DECREF(field);
      return false;
    }
    if (!task_msgs__msg__MedicineData__Sequence__init(&(ros_message->medicine_list), size)) {
      PyErr_SetString(PyExc_RuntimeError, "unable to create task_msgs__msg__MedicineData__Sequence ros_message");
      Py_DECREF(seq_field);
      Py_DECREF(field);
      return false;
    }
    task_msgs__msg__MedicineData * dest = ros_message->medicine_list.data;
    for (Py_ssize_t i = 0; i < size; ++i) {
      if (!task_msgs__msg__medicine_data__convert_from_py(PySequence_Fast_GET_ITEM(seq_field, i), &dest[i])) {
        Py_DECREF(seq_field);
        Py_DECREF(field);
        return false;
      }
    }
    Py_DECREF(seq_field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * task_msgs__msg__cabinet_state__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of CabinetState */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("task_msgs.msg._cabinet_state");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "CabinetState");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  task_msgs__msg__CabinetState * ros_message = (task_msgs__msg__CabinetState *)raw_ros_message;
  {  // cabinet_id
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->cabinet_id);
    {
      int rc = PyObject_SetAttrString(_pymessage, "cabinet_id", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // medicine_list
    PyObject * field = NULL;
    size_t size = ros_message->medicine_list.size;
    field = PyList_New(size);
    if (!field) {
      return NULL;
    }
    task_msgs__msg__MedicineData * item;
    for (size_t i = 0; i < size; ++i) {
      item = &(ros_message->medicine_list.data[i]);
      PyObject * pyitem = task_msgs__msg__medicine_data__convert_to_py(item);
      if (!pyitem) {
        Py_DECREF(field);
        return NULL;
      }
      int rc = PyList_SetItem(field, i, pyitem);
      (void)rc;
      assert(rc == 0);
    }
    assert(PySequence_Check(field));
    {
      int rc = PyObject_SetAttrString(_pymessage, "medicine_list", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
