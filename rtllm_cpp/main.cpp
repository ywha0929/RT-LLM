#define PY_SSIZE_T_CLEAN
// #include "/usr/include/python3.10/Python.h"
#include <Python.h>

#include <filesystem>
#include <iostream>

int main(int argc, char *argv[]) {
    std::filesystem::path script(argv[0]);
    Py_Initialize();
    PyObject * sysPath = PySys_GetObject("path");
    PyList_Insert(sysPath, 0, PyUnicode_FromString(script.parent_path().c_str()));
    PyObject * pModule = PyImport_ImportModule("Answerer/Answerer");
    PyObject * pClass = PyObject_GetAttrString(pModule, "Answerer");
    PyObject * pObj = PyObject_CallObject(pClass, nullptr);
    PyObject * pMethod = PyObject_GetAttrString(pObj, "ask");
    PyObject_CallFunction(pMethod, "ff", 2.0, 5.0);
    Py_Finalize();
    
}