set(BAYCOM_TOOLS
    baycom_test
    baycom_sethdlc
    baycom_kissbridge
    baycom_kiss_serial
)

add_executable(baycom_test baycom_test.c)
add_executable(baycom_sethdlc baycom_sethdlc.c)
add_executable(baycom_kissbridge baycom_kissbridge.c)
target_link_libraries(baycom_kissbridge PRIVATE util)

add_executable(baycom_kiss_serial baycom_kiss_serial.c)
target_link_libraries(baycom_kiss_serial PRIVATE util)

foreach(tool IN LISTS BAYCOM_TOOLS)
    target_compile_options(${tool} PRIVATE -O2 -Wall -Wextra)
endforeach()

install(TARGETS ${BAYCOM_TOOLS} RUNTIME DESTINATION "${CMAKE_INSTALL_SBINDIR}")
