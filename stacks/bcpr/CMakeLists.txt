# stacks/bcpr — BayCom/based SER12 userspace (MAX25 plugin)
cmake_minimum_required(VERSION 3.16)
project(bcpr VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

include(GNUInstallDirs)

set(BCPR_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(BCPR_LIB_SRCS
    src/bcpr_crc.c
    src/bcpr_hdlc.c
    src/bcpr_ser12.c
    src/bcpr_uart.c
    src/bcpr_lock.c
    src/bcpr_config.c
    src/bcpr_engine.c
)

add_library(bcpr STATIC ${BCPR_LIB_SRCS})
target_include_directories(bcpr PUBLIC "${BCPR_ROOT}/include")
target_compile_options(bcpr PRIVATE -Wall -Wextra -Wno-unused-parameter)

add_executable(bcprd src/bcprd.c)
find_package(Threads REQUIRED)
target_link_libraries(bcprd PRIVATE bcpr util Threads::Threads)
target_include_directories(bcprd PRIVATE "${BCPR_ROOT}/include")

add_executable(test_hdlc_offline tests/test_hdlc_offline.c)
target_link_libraries(test_hdlc_offline PRIVATE bcpr)
target_include_directories(test_hdlc_offline PRIVATE "${BCPR_ROOT}/include")

add_executable(test_config_offline tests/test_config_offline.c)
target_link_libraries(test_config_offline PRIVATE bcpr)
target_include_directories(test_config_offline PRIVATE "${BCPR_ROOT}/include")

enable_testing()
add_test(NAME bcpr_hdlc_offline COMMAND test_hdlc_offline)
set_tests_properties(bcpr_hdlc_offline PROPERTIES LABELS "bcpr")
add_test(NAME bcpr_config_offline
         COMMAND test_config_offline
         WORKING_DIRECTORY "${BCPR_ROOT}")
set_tests_properties(bcpr_config_offline PROPERTIES LABELS "bcpr")

install(TARGETS bcprd RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
install(TARGETS bcpr ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}")
install(DIRECTORY "${BCPR_ROOT}/include/bcpr"
        DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}")
install(PROGRAMS "${BCPR_ROOT}/tools/bcpr-ctl"
                "${BCPR_ROOT}/tools/bcpr-rxtx-smoke.sh"
        DESTINATION "${CMAKE_INSTALL_SBINDIR}")
install(FILES "${BCPR_ROOT}/share/bcpr.ini.example"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/bcpr")
install(FILES "${BCPR_ROOT}/NOTICE.md" "${BCPR_ROOT}/VERSION"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/bcpr")

message(STATUS "bcpr ${PROJECT_VERSION} — SER12 userspace (max25e0)")
