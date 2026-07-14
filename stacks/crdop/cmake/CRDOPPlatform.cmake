# CRDOP platform / architecture detection (standalone project)
#
# Tested: Linux, *BSD, Windows, macOS — GCC and Clang/LLVM

if(CMAKE_SYSTEM_PROCESSOR MATCHES "^(aarch64|arm64)$")
    set(CRDOP_ARCH "aarch64")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(armv7|armv7l|arm)$")
    set(CRDOP_ARCH "arm32")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(i[3-6]86)$")
    set(CRDOP_ARCH "x86")
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "^(x86_64|AMD64)$")
    set(CRDOP_ARCH "x86_64")
else()
    set(CRDOP_ARCH "${CMAKE_SYSTEM_PROCESSOR}")
endif()

set(CRDOP_PLATFORM_INCLUDES "")
set(CRDOP_PLATFORM_LIBS "")
set(CRDOP_PLATFORM_SOURCES "")

if(WIN32)
    set(CRDOP_PLATFORM "windows")
    set(CRDOP_PLATFORM_SOURCES
        src/windows/Waveout.c
        lib/hid/hid.c
    )
    set(CRDOP_PLATFORM_LIBS wsock32 winmm setupapi ws2_32)
elseif(APPLE)
    set(CRDOP_PLATFORM "darwin")
    set(CRDOP_PLATFORM_SOURCES
        src/linux/ALSASound.c
        src/linux/LinSerial.c
        src/darwin/alsa_shim.c
    )
    list(APPEND CRDOP_PLATFORM_INCLUDES "${VENDOR_DIR}/src")
    find_library(CRDOP_COREAUDIO_LIB CoreAudio REQUIRED)
    find_library(CRDOP_AUDIOTOOLBOX_LIB AudioToolbox REQUIRED)
    find_library(CRDOP_COREFOUNDATION_LIB CoreFoundation REQUIRED)
    set(CRDOP_PLATFORM_LIBS
        ${CRDOP_COREAUDIO_LIB}
        ${CRDOP_AUDIOTOOLBOX_LIB}
        ${CRDOP_COREFOUNDATION_LIB}
        pthread m
    )
elseif(CMAKE_SYSTEM_NAME STREQUAL "FreeBSD")
    set(CRDOP_PLATFORM "freebsd-oss")
    set(CRDOP_PLATFORM_SOURCES
        src/linux/LinSerial.c
    )
    set(CRDOP_PLATFORM_LIBS pthread m)
elseif(CMAKE_SYSTEM_NAME MATCHES "OpenBSD|NetBSD|DragonFly")
    set(CRDOP_PLATFORM "bsd-oss")
    set(CRDOP_PLATFORM_SOURCES
        src/linux/LinSerial.c
    )
    set(CRDOP_PLATFORM_LIBS pthread m)
elseif(UNIX)
    set(CRDOP_PLATFORM "linux")
    set(CRDOP_PLATFORM_SOURCES
        src/linux/ALSASound.c
        src/linux/LinSerial.c
    )
    find_package(PkgConfig REQUIRED)
    pkg_check_modules(ALSA REQUIRED alsa)
    set(CRDOP_PLATFORM_INCLUDES ${ALSA_INCLUDE_DIRS})
    set(CRDOP_PLATFORM_LIBS ${ALSA_LIBRARIES} rt pthread m)
else()
    message(FATAL_ERROR "CRDOP: unsupported system ${CMAKE_SYSTEM_NAME}")
endif()

message(STATUS "CRDOP platform=${CRDOP_PLATFORM} arch=${CRDOP_ARCH} system=${CMAKE_SYSTEM_NAME}")
