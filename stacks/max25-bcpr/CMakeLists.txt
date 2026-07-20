# stacks/max25-bcpr — BayCom/based SER12 userspace (MAX25 plugin)
# Product face: max25-bcpr / max25-bcprd. Internal C API still uses bcpr_* symbols.
cmake_minimum_required(VERSION 3.16)
project(max25_bcpr VERSION 0.1.0 LANGUAGES C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

include(GNUInstallDirs)

set(MAX25_BCPR_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(MAX25_BCPR_LIB_SRCS
    src/bcpr_crc.c
    src/bcpr_hdlc.c
    src/bcpr_ser12.c
    src/bcpr_uart.c
    src/bcpr_lock.c
    src/bcpr_config.c
    src/bcpr_engine.c
)

add_library(max25_bcpr_lib STATIC ${MAX25_BCPR_LIB_SRCS})
target_include_directories(max25_bcpr_lib PUBLIC "${MAX25_BCPR_ROOT}/include")
target_compile_options(max25_bcpr_lib PRIVATE -Wall -Wextra -Wno-unused-parameter)

add_executable(max25-bcprd src/max25-bcprd.c)
find_package(Threads REQUIRED)
target_link_libraries(max25-bcprd PRIVATE max25_bcpr_lib util Threads::Threads)
target_include_directories(max25-bcprd PRIVATE "${MAX25_BCPR_ROOT}/include")

add_executable(test_hdlc_offline tests/test_hdlc_offline.c)
target_link_libraries(test_hdlc_offline PRIVATE max25_bcpr_lib)
target_include_directories(test_hdlc_offline PRIVATE "${MAX25_BCPR_ROOT}/include")

add_executable(test_config_offline tests/test_config_offline.c)
target_link_libraries(test_config_offline PRIVATE max25_bcpr_lib)
target_include_directories(test_config_offline PRIVATE "${MAX25_BCPR_ROOT}/include")

enable_testing()
add_test(NAME max25_bcpr_hdlc_offline COMMAND test_hdlc_offline)
set_tests_properties(max25_bcpr_hdlc_offline PROPERTIES LABELS "max25-bcpr")
add_test(NAME max25_bcpr_config_offline
         COMMAND test_config_offline
         WORKING_DIRECTORY "${MAX25_BCPR_ROOT}")
set_tests_properties(max25_bcpr_config_offline PROPERTIES LABELS "max25-bcpr")

install(TARGETS max25-bcprd RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
install(TARGETS max25_bcpr_lib ARCHIVE DESTINATION "${CMAKE_INSTALL_LIBDIR}")
install(DIRECTORY "${MAX25_BCPR_ROOT}/include/bcpr"
        DESTINATION "${CMAKE_INSTALL_INCLUDEDIR}")
install(PROGRAMS "${MAX25_BCPR_ROOT}/tools/max25-bcpr-ctl"
                "${MAX25_BCPR_ROOT}/tools/max25-bcpr-rxtx-smoke.sh"
        DESTINATION "${CMAKE_INSTALL_SBINDIR}")
install(FILES "${MAX25_BCPR_ROOT}/share/max25-bcpr.ini.example"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/max25-bcpr")
install(FILES "${MAX25_BCPR_ROOT}/NOTICE.md" "${MAX25_BCPR_ROOT}/VERSION"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/max25-bcpr")

message(STATUS "max25-bcpr ${PROJECT_VERSION} — SER12 userspace (max25e0; not usable by default)")
