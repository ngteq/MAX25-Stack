cmake_minimum_required(VERSION 3.16)
# Product label CRDOP-CUR999 (pre-release until v0.5). CMake project() requires a
# numeric VERSION; 0.0.999 is the build-time fallback. Human-facing strings live
# in VERSION (CUR999) and include/crdop/version.h (CRDOP-CUR999 / CUR999).
project(crdop VERSION 0.0.999 LANGUAGES C)

set(CMAKE_C_STANDARD 17)
set(CMAKE_C_STANDARD_REQUIRED ON)

include(GNUInstallDirs)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

option(CRDOP_VENDOR_ARDOPCF
       "Dev-only: build legacy ARDOP (ardopcf) vendor — OFF by default; never installed in MAX25 releases"
       OFF)

set(CRDOP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}")
set(VENDOR_DIR "${CRDOP_ROOT}/vendor/ardopcf")

function(crdop_install_scaffold)
    install(FILES
        "${CRDOP_ROOT}/share/crdop.ini.example"
        "${CRDOP_ROOT}/share/crdop-dual.ini.example"
        "${CRDOP_ROOT}/share/crdop-amateur.ini.example"
        DESTINATION ${CMAKE_INSTALL_DATADIR}/crdop
    )
    install(FILES "${CRDOP_ROOT}/VERSION" DESTINATION ${CMAKE_INSTALL_DATADIR}/crdop)
    install(PROGRAMS "${CRDOP_ROOT}/scripts/crdopc"
            DESTINATION ${CMAKE_INSTALL_BINDIR} RENAME crdop)
    install(PROGRAMS
        "${CRDOP_ROOT}/tools/max25-signal-sniffer"
        "${CRDOP_ROOT}/tools/audio-dummyd"
        DESTINATION ${CMAKE_INSTALL_BINDIR}
    )
    install(DIRECTORY "${CRDOP_ROOT}/lib/"
            DESTINATION ${CMAKE_INSTALL_DATADIR}/crdop/lib
            FILES_MATCHING PATTERN "*.py")
endfunction()

if(CRDOP_VENDOR_ARDOPCF AND EXISTS "${VENDOR_DIR}/Makefile")
    include("${CRDOP_ROOT}/cmake/CRDOPVendorArdopcf.cmake")
    crdop_install_scaffold()
    message(STATUS "CRDOP ${PROJECT_VERSION} → crdopc (legacy vendor/ardopcf)")
elseif(CRDOP_VENDOR_ARDOPCF)
    message(WARNING "CRDOP: CRDOP_VENDOR_ARDOPCF=ON but vendor/ardopcf missing — scaffold only")
    crdop_install_scaffold()
    message(STATUS "CRDOP: scaffold only (native modem in development)")
else()
    crdop_install_scaffold()
    message(STATUS "CRDOP: scaffold only (native Eigenentwicklung; -DCRDOP_VENDOR_ARDOPCF=ON for legacy vendor build)")
endif()
