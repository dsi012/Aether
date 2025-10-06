#
# MCP Interface Application CMakeLists.txt
#
# This CMake file builds the MCP Interface Application for cFS
#

# Set minimum CMake version
cmake_minimum_required(VERSION 3.5)

# Project name
project(MCP_INTERFACE_APP)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${cfe_MISSION_DIR}/cfe/fsw/inc
    ${MISSION_SOURCE_DIR}/psp/fsw/inc
    ${MISSION_SOURCE_DIR}/osal/src/os/inc
)

# Source files
set(APP_SRC_FILES
    mcp_interface_app.c
    mcp_command_handlers.c
    mcp_safety_utils.c
)

# Create the app
add_cfe_app(mcp_interface ${APP_SRC_FILES})

# Link with required libraries
target_link_libraries(mcp_interface cjson)

# Install the app
install(TARGETS mcp_interface DESTINATION ${INSTALL_SUBDIR})

# Install header files
install(FILES mcp_interface_app.h DESTINATION ${INSTALL_SUBDIR})

# Create version information
configure_file(
    ${CMAKE_CURRENT_SOURCE_DIR}/mcp_interface_version.h.in
    ${CMAKE_CURRENT_BINARY_DIR}/mcp_interface_version.h
    @ONLY
)

# Add version header to include path
target_include_directories(mcp_interface PRIVATE ${CMAKE_CURRENT_BINARY_DIR})
