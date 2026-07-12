# CRDOP compiler detection and warning flags (GCC, Clang, MSVC)

if(CMAKE_C_COMPILER_ID STREQUAL "GNU")
    set(CRDOP_COMPILER "gcc")
elseif(CMAKE_C_COMPILER_ID MATCHES "Clang|AppleClang")
    set(CRDOP_COMPILER "clang")
elseif(MSVC)
    set(CRDOP_COMPILER "msvc")
else()
    set(CRDOP_COMPILER "${CMAKE_C_COMPILER_ID}")
endif()

message(STATUS "CRDOP compiler=${CRDOP_COMPILER} (${CMAKE_C_COMPILER_ID} ${CMAKE_C_COMPILER_VERSION})")

function(crdop_set_compile_options target)
    if(MSVC)
        target_compile_options(${target} PRIVATE /W3 /utf-8)
    else()
        target_compile_options(${target} PRIVATE -Wall -Wextra -Wno-unused-parameter)
        if(CRDOP_COMPILER STREQUAL "clang")
            target_compile_options(${target} PRIVATE
                -Wno-gnu-zero-variadic-macro-arguments
                -Wno-deprecated-non-prototype
            )
        endif()
        if(CMAKE_BUILD_TYPE STREQUAL "Release")
            target_compile_options(${target} PRIVATE -O2)
        endif()
    endif()
endfunction()

include(CheckLinkerFlag)
if(NOT WIN32 AND NOT APPLE)
    check_linker_flag(C "-Wl,--wrap=malloc" CRDOP_LINKER_SUPPORTS_WRAP)
else()
    set(CRDOP_LINKER_SUPPORTS_WRAP FALSE)
endif()
