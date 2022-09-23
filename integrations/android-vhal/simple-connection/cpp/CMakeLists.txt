

project(grpc_connection C CXX)
cmake_minimum_required(VERSION 3.10)

include(FindProtobuf)
find_package(Protobuf REQUIRED)
include_directories(${PROTOBUF_INCLUDE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/proto_files)

add_executable(${PROJECT_NAME}
    connection.cc
    proto_files/common.pb.cc
    proto_files/network_api.pb.cc
    proto_files/network_api.grpc.pb.cc
)

set_property(TARGET ${PROJECT_NAME} PROPERTY CXX_STANDARD 14)

target_link_libraries(${PROJECT_NAME} PRIVATE 
    ${PROTOBUF_LIBRARY}
    grpc
    grpc++
    pthread
)
