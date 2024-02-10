cmake_minimum_required(VERSION 3.5)
project(void_pointer)
find_package(catkin REQUIRED)
catkin_python_setup()

execute_process(
  COMMAND app/void_pointer_ws/src/void_pointer/scripts/gRPC_bash.sh
  RESULT_VARIABLE script_result
  OUTPUT_VARIABLE script_output
)

message(STATUS "gRPC bindings generation result: ${script_result}")
message(STATUS "gRPC bindings generation output: ${script_output}")