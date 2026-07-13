# Legacy vendor/ardopcf build (opt-in only; not shipped in MAX25 v1).

include("${CRDOP_ROOT}/cmake/CRDOPCompiler.cmake")
include("${CRDOP_ROOT}/cmake/CRDOPPlatform.cmake")

option(CRDOP_BUILD_TESTS "Build upstream ardopcf cmocka unit tests" OFF)

set(CRDOP_VENDOR_COMMON
    lib/rawhid/rawhid.c
    lib/rockliff/rrs.c
    lib/ws_server/ws_server.c
    src/common/ARDOPC.c
    src/common/ARDOPCommon.c
    src/common/ardopSampleArrays.c
    src/common/ARQ.c
    src/common/BusyDetect.c
    src/common/FEC.c
    src/common/FFT.c
    src/common/HostInterface.c
    src/common/Locator.c
    src/common/log_file.c
    src/common/log.c
    src/common/Modulate.c
    src/common/Packed6.c
    src/common/RXO.c
    src/common/sdft.c
    src/common/SoundInput.c
    src/common/StationId.c
    src/common/TCPHostInterface.c
    src/common/txframe.c
    src/common/wav.c
    src/common/Webgui.c
    src/common/noise.c
    src/common/ardopcf.c
)

set(CRDOP_VENDOR_SRCS "")
foreach(rel IN LISTS CRDOP_VENDOR_COMMON CRDOP_PLATFORM_SOURCES)
    list(APPEND CRDOP_VENDOR_SRCS "${VENDOR_DIR}/${rel}")
endforeach()

set(TXT2C "${CMAKE_BINARY_DIR}/txt2c")
add_executable(txt2c "${VENDOR_DIR}/lib/txt2c/txt2c.c")
crdop_set_compile_options(txt2c)
set_target_properties(txt2c PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}")

set(WEBGUI_HTML_C "${CMAKE_BINARY_DIR}/gen-webgui.html.c")
set(WEBGUI_JS_C "${CMAKE_BINARY_DIR}/gen-webgui.js.c")
add_custom_command(
    OUTPUT "${WEBGUI_HTML_C}"
    COMMAND txt2c "${VENDOR_DIR}/webgui/webgui.html" "${WEBGUI_HTML_C}" webgui_html
    DEPENDS txt2c "${VENDOR_DIR}/webgui/webgui.html"
    COMMENT "Embedding webgui.html"
)
add_custom_command(
    OUTPUT "${WEBGUI_JS_C}"
    COMMAND txt2c "${VENDOR_DIR}/webgui/webgui.js" "${WEBGUI_JS_C}" webgui_js
    DEPENDS txt2c "${VENDOR_DIR}/webgui/webgui.js"
    COMMENT "Embedding webgui.js"
)

add_library(ardopcf_vendor_objs OBJECT
    ${CRDOP_VENDOR_SRCS}
    "${WEBGUI_HTML_C}"
    "${WEBGUI_JS_C}"
)

target_include_directories(ardopcf_vendor_objs PRIVATE
    "${CRDOP_ROOT}/include"
    "${VENDOR_DIR}/src"
    "${VENDOR_DIR}/lib"
    ${CRDOP_PLATFORM_INCLUDES}
)

target_compile_definitions(ardopcf_vendor_objs PRIVATE CRDOP_BUILD=1)

if(WIN32)
    target_compile_definitions(ardopcf_vendor_objs PRIVATE WIN32 _CRT_SECURE_NO_DEPRECATE)
endif()

if(APPLE)
    target_compile_definitions(ardopcf_vendor_objs PRIVATE __APPLE__)
endif()

crdop_set_compile_options(ardopcf_vendor_objs)

add_executable(crdopc
    "${CRDOP_ROOT}/src/crdop_version.c"
    $<TARGET_OBJECTS:ardopcf_vendor_objs>
)

target_include_directories(crdopc PRIVATE
    "${CRDOP_ROOT}/include"
    "${VENDOR_DIR}/src"
    "${VENDOR_DIR}/lib"
    ${CRDOP_PLATFORM_INCLUDES}
)

target_compile_definitions(crdopc PRIVATE CRDOP_BUILD=1)

if(WIN32)
    target_compile_definitions(crdopc PRIVATE WIN32 _CRT_SECURE_NO_DEPRECATE)
endif()

if(APPLE)
    target_compile_definitions(crdopc PRIVATE __APPLE__)
endif()

crdop_set_compile_options(crdopc)
target_link_libraries(crdopc PRIVATE ${CRDOP_PLATFORM_LIBS})

add_library(ardopcf_vendor STATIC
    "${CRDOP_ROOT}/src/crdop_version.c"
    $<TARGET_OBJECTS:ardopcf_vendor_objs>
)
target_include_directories(ardopcf_vendor PUBLIC
    "${CRDOP_ROOT}/include"
    "${VENDOR_DIR}/src"
    "${VENDOR_DIR}/lib"
    ${CRDOP_PLATFORM_INCLUDES}
)
target_compile_definitions(ardopcf_vendor PUBLIC CRDOP_BUILD=1)
target_link_libraries(ardopcf_vendor PUBLIC ${CRDOP_PLATFORM_LIBS})

include("${CRDOP_ROOT}/cmake/CRDOPTests.cmake")

install(TARGETS crdopc RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
