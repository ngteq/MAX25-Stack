cmake_minimum_required(VERSION 3.16)
project(MainAX25Stack VERSION 1.5.0 LANGUAGES C)

include(GNUInstallDirs)
enable_testing()

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
include(MAX25Platform)
include(MAX25Ax25)

option(MAX25_BUILD_TNCS "Build stacks/tncs tools" ON)
option(MAX25_BUILD_CRDOP "Build and install MAX25-SoftModem (CRDOP) — disable only if not needed" ON)
option(MAX25_BUILD_MAX25_BCPR "Build stacks/max25-bcpr BayCom/based SER12 (experimental; default OFF — not usable)" OFF)
# Legacy alias: -DMAX25_BUILD_BCPR still accepted
if(DEFINED MAX25_BUILD_BCPR)
    set(MAX25_BUILD_MAX25_BCPR "${MAX25_BUILD_BCPR}" CACHE BOOL "Build max25-bcpr (legacy MAX25_BUILD_BCPR)" FORCE)
endif()
option(MAX25_BUILD_TERMINAL "Build max25-terminal / max25-client" ON)
option(MAX25_BUILD_DAEMON "Install max25d" ON)
option(MAX25_BUILD_WEB "Install MAX25 web UI scaffold" ON)
# Legacy kernel baycom-pr removed 2026-07-18 → vault archives/legacy/max25-stack-baycom-kernel-compa/

if(MAX25_BUILD_TNCS)
    add_subdirectory(stacks/tncs)
endif()

if(MAX25_BUILD_CRDOP)
    add_subdirectory(stacks/crdop "${CMAKE_BINARY_DIR}/crdop")
endif()

if(MAX25_BUILD_MAX25_BCPR)
    add_subdirectory(stacks/max25-bcpr "${CMAKE_BINARY_DIR}/max25-bcpr")
endif()

if(MAX25_BUILD_TERMINAL)
    add_subdirectory(stacks/terminal)
endif()

if(MAX25_BUILD_WEB)
    add_subdirectory(stacks/web)
endif()

if(MAX25_BUILD_DAEMON)
    execute_process(
        COMMAND "${CMAKE_COMMAND}" -E chmod u+x
                "${CMAKE_SOURCE_DIR}/stacks/daemon/max25d"
                "${CMAKE_SOURCE_DIR}/stacks/daemon/max25d.py"
        ERROR_QUIET
    )
    install(PROGRAMS "${CMAKE_SOURCE_DIR}/stacks/daemon/max25d"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(PROGRAMS "${CMAKE_SOURCE_DIR}/stacks/daemon/max25d.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/daemon_log.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/kiss_bridge.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/ax25_codec.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/device_backends.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/banlist.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/reporting_quality.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/paths.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/max25_platform.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/modular_tcp_server.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    if(MAX25_BUILD_TNCS)
        set(_MAX25_STACK_PROGRAMS
            stacks/tncs/load-serial-env.sh
            stacks/tncs/tnc2c-boot-wait.sh
            stacks/tncs/tnc2c-host-reset.sh
            stacks/tncs/pktnc2-boot-wait.sh
        )
        set(_MAX25_STACK_DATA
            stacks/tncs/tnc2c-boot-wait.py
            stacks/tncs/tnc2c-host-reset.py
            stacks/tncs/tnc_serial_recovery.py
            stacks/tncs/tnc2c-serial.env
            stacks/tncs/pktnc2-serial.env
        )
        foreach(_script IN LISTS _MAX25_STACK_PROGRAMS)
            get_filename_component(_dir "${_script}" DIRECTORY)
            string(REPLACE "stacks/" "" _rel "${_dir}")
            install(PROGRAMS "${CMAKE_SOURCE_DIR}/${_script}"
                    DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/stacks/${_rel}")
        endforeach()
        foreach(_script IN LISTS _MAX25_STACK_DATA)
            get_filename_component(_dir "${_script}" DIRECTORY)
            string(REPLACE "stacks/" "" _rel "${_dir}")
            install(FILES "${CMAKE_SOURCE_DIR}/${_script}"
                    DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/stacks/${_rel}")
        endforeach()
    endif()
endif()

install(PROGRAMS "${CMAKE_SOURCE_DIR}/scripts/max25-ctl"
        DESTINATION "${CMAKE_INSTALL_BINDIR}")
install(PROGRAMS "${CMAKE_SOURCE_DIR}/scripts/max25d-session.sh"
        DESTINATION "${CMAKE_INSTALL_BINDIR}" RENAME max25d-session)

install(FILES
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.ini.host.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.full-station.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.netdev.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.freebsd.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.main.ini.example"
    DESTINATION "${CMAKE_INSTALL_DATADIR}/max25"
)

# share/baycom/README.md only — kernel INI examples removed; use share/max25-bcpr/
if(EXISTS "${CMAKE_SOURCE_DIR}/share/baycom/README.md")
    install(FILES "${CMAKE_SOURCE_DIR}/share/baycom/README.md"
            DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/baycom")
endif()

if(MAX25_BUILD_MAX25_BCPR)
    install(PROGRAMS "${CMAKE_SOURCE_DIR}/stacks/max25-bcpr/tools/max25-bcpr-ctl"
            DESTINATION "${CMAKE_INSTALL_SBINDIR}")
endif()

if(EXISTS "${CMAKE_SOURCE_DIR}/share/max25/max25d.service.example")
    install(FILES "${CMAKE_SOURCE_DIR}/share/max25/max25d.service.example"
            DESTINATION "${CMAKE_INSTALL_DATADIR}/max25")
endif()

add_custom_target(max25_release_check
    COMMAND "${CMAKE_SOURCE_DIR}/scripts/release-check.sh"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    USES_TERMINAL
    COMMENT "Run offline release-check gates"
)

if(TARGET crdopc)
    add_custom_target(crdop_smoke
        COMMAND "${CMAKE_COMMAND}" -E env CRDOP_BIN="${CMAKE_BINARY_DIR}/bin/crdopc"
                bash "${CMAKE_SOURCE_DIR}/stacks/crdop/scripts/test-smoke.sh"
        DEPENDS crdopc
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        COMMENT "CRDOP smoke test"
    )
endif()

add_custom_target(max25_daemon_smoke
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_paths.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_proto.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_auth.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_ax25_codec.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_kiss_bridge.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_baycom_backend.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_bcpr_backend.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_crdop_backend.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_multi_device.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_bans.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/tncs/test_tnc_serial_recovery.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_audio_dummy_backend.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_modular_tcp.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_max25_platform.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_serial_watch.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_daemon_log.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_reporting.py"
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${CMAKE_SOURCE_DIR}/stacks/daemon/test_reporting_quality.py"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    COMMENT "max25d M25/1 smoke tests"
)

# Unified TX/RX release test (L0 offline) — TNC + BayCom/based (bcpr)
add_custom_target(max25_tx_rx_test
    COMMAND bash "${CMAKE_SOURCE_DIR}/scripts/tx-rx-test.sh"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    USES_TERMINAL
    COMMENT "TX/RX L0 offline (TNC + BayCom/based bcpr)"
)
add_test(NAME max25_tx_rx_offline
         COMMAND bash "${CMAKE_SOURCE_DIR}/scripts/tx-rx-test.sh"
         WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}")
set_tests_properties(max25_tx_rx_offline PROPERTIES LABELS "txrx;offline")

if(TARGET max25-terminal)
    add_custom_target(max25_terminal_test
        COMMAND bash "${CMAKE_SOURCE_DIR}/stacks/terminal/test-terminal.sh"
        DEPENDS max25-terminal
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        COMMENT "max25-terminal TCP probe"
    )
endif()


add_custom_target(max25_test
    DEPENDS max25_daemon_smoke max25_tx_rx_test
)

if(TARGET max25-terminal)
    add_dependencies(max25_test max25_terminal_test)
endif()

if(TARGET crdop_smoke)
    add_dependencies(max25_test crdop_smoke)
endif()

if(TARGET max25_web_smoke)
    add_dependencies(max25_test max25_web_smoke)
endif()

message(STATUS "MainAX25-Stack → ${CMAKE_BINARY_DIR}/bin (install prefix: ${CMAKE_INSTALL_PREFIX})")
