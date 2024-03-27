
cmake_minimum_required(VERSION 3.15...3.27)
project(ctp_wrapper) # Replace 'my_project' with the name of your project
find_package(Python 3.8 COMPONENTS Interpreter Development.Module REQUIRED)
if (NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Choose the type of build." FORCE)
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS "Debug" "Release" "MinSizeRel" "RelWithDebInfo")
endif()
link_directories(${CMAKE_SOURCE_DIR})
# Detect the installed nanobind package and import it into CMake
# add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/ext/nanobind)
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE OUTPUT_VARIABLE NB_DIR)
list(APPEND CMAKE_PREFIX_PATH "${NB_DIR}")
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(ext_foo_bar ${CMAKE_SOURCE_DIR}/src/foo_bar.cpp)
nanobind_add_module(ext_foo ${CMAKE_SOURCE_DIR}/src/foo.cpp)
nanobind_add_stub(
  ext_foo_stub
    MODULE ext_foo
    OUTPUT ext_foo.pyi
    PYTHON_PATH $<TARGET_FILE_DIR:ext_foo>
    # DEPENDS ext_foo
    VERBOSE
)
nanobind_add_stub(
  ext_foo_bar_stub
    MODULE ext_foo_bar
    OUTPUT ext_foo_bar.pyi
    PYTHON_PATH $<TARGET_FILE_DIR:ext_foo_bar>
    # DEPENDS ext_foo_bar
    VERBOSE
)