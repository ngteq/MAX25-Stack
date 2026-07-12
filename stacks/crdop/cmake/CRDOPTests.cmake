# Upstream ardopcf cmocka unit tests (Unix + GNU/Clang ld --wrap)

option(CRDOP_BUILD_TESTS "Build and register upstream ardopcf unit tests" OFF)

if(NOT CRDOP_BUILD_TESTS)
    return()
endif()

if(WIN32 OR APPLE)
    message(STATUS "CRDOP_BUILD_TESTS: skipped on ${CRDOP_PLATFORM} (cmocka/--wrap needs Unix GNU or lld linker)")
    return()
endif()

find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(CMOCKA QUIET cmocka)
endif()

if(NOT CMOCKA_FOUND)
    find_path(CMOCKA_INCLUDE_DIR cmocka.h)
    find_library(CMOCKA_LIBRARY cmocka)
    if(CMOCKA_INCLUDE_DIR AND CMOCKA_LIBRARY)
        set(CMOCKA_FOUND TRUE)
        set(CMOCKA_INCLUDE_DIRS "${CMOCKA_INCLUDE_DIR}")
        set(CMOCKA_LIBRARIES "${CMOCKA_LIBRARY}")
    endif()
endif()

if(NOT CMOCKA_FOUND)
    message(WARNING "CRDOP_BUILD_TESTS: libcmocka not found — install cmocka dev package (see docs/BUILD.md)")
    return()
endif()

if(NOT CRDOP_LINKER_SUPPORTS_WRAP)
    message(WARNING "CRDOP_BUILD_TESTS: linker does not support --wrap; unit tests disabled")
    return()
endif()

enable_testing()

set(CRDOP_VENDOR_TEST_DIR "${VENDOR_DIR}/test/ardop")
set(CRDOP_VENDOR_TEST_COMMON
    "${CRDOP_VENDOR_TEST_DIR}/setup.c"
)

function(crdop_add_vendor_test name)
    cmake_parse_arguments(ARG "" "" "SOURCES;WRAP" ${ARGN})
    set(test_src "${CRDOP_VENDOR_TEST_DIR}/test_${name}.c")
    if(NOT EXISTS "${test_src}")
        message(FATAL_ERROR "CRDOP test source missing: ${test_src}")
    endif()

    set(sources "${test_src}" ${CRDOP_VENDOR_TEST_COMMON})
    if(ARG_SOURCES)
        foreach(rel IN LISTS ARG_SOURCES)
            list(APPEND sources "${VENDOR_DIR}/${rel}")
        endforeach()
    endif()

    add_executable(crdop_test_${name} ${sources})
    crdop_set_compile_options(crdop_test_${name})

    target_include_directories(crdop_test_${name} PRIVATE
        "${CRDOP_ROOT}/include"
        "${VENDOR_DIR}/src"
        "${VENDOR_DIR}/lib"
        ${CRDOP_PLATFORM_INCLUDES}
    )

    if(ARG_SOURCES)
        target_link_libraries(crdop_test_${name} PRIVATE m pthread)
        if(CRDOP_PLATFORM STREQUAL "linux")
            target_link_libraries(crdop_test_${name} PRIVATE rt)
        endif()
    else()
        target_link_libraries(crdop_test_${name} PRIVATE ardopcf_vendor)
    endif()

    target_link_libraries(crdop_test_${name} PRIVATE ${CMOCKA_LIBRARIES})
    target_include_directories(crdop_test_${name} PRIVATE ${CMOCKA_INCLUDE_DIRS})

    if(ARG_WRAP)
        foreach(sym IN LISTS ARG_WRAP)
            target_link_options(crdop_test_${name} PRIVATE "-Wl,--wrap=${sym}")
        endforeach()
    endif()

    add_test(NAME crdop_test_${name} COMMAND crdop_test_${name})
endfunction()

crdop_add_vendor_test(ARDOPCommon)
crdop_add_vendor_test(HostInterface)
crdop_add_vendor_test(Locator)
crdop_add_vendor_test(Packed6)
crdop_add_vendor_test(StationId)
crdop_add_vendor_test(log
    SOURCES
        src/common/log_file.c
        src/common/log.c
    WRAP
        fopen fclose fwrite fflush freopen
)

message(STATUS "CRDOP_BUILD_TESTS: registered upstream ardopcf cmocka tests")
