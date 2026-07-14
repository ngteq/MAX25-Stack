cmake_minimum_required(VERSION 3.16)
project(MainAX25Stack VERSION 1.5.0 LANGUAGES C)

include(GNUInstallDirs)

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
option(MAX25_BUILD_BAYCOM "Build stacks/baycom-pr tools (runtime default off via [features])" ON)
option(MAX25_BUILD_CRDOP "Build and install MAX25-SoftModem (CRDOP) — disable only if not needed" ON)
option(MAX25_BUILD_TERMINAL "Build max25-terminal / max25-client" ON)
option(MAX25_BUILD_DAEMON "Install max25d" ON)
option(MAX25_BUILD_WEB "Install MAX25 web UI scaffold" ON)

if(MAX25_BUILD_TNCS)
    add_subdirectory(stacks/tncs)
endif()

if(MAX25_BUILD_BAYCOM)
    add_subdirectory(stacks/baycom-pr/tools)
endif()

if(MAX25_BUILD_CRDOP)
    add_subdirectory(stacks/crdop "${CMAKE_BINARY_DIR}/crdop")
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
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.dual-baycom.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.netdev.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.freebsd.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.main.ini.example"
    DESTINATION "${CMAKE_INSTALL_DATADIR}/max25"
)

if(MAX25_BUILD_BAYCOM)
install(DIRECTORY "${CMAKE_SOURCE_DIR}/share/baycom/"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/baycom"
        FILES_MATCHING PATTERN "*.example" PATTERN "README.md")

install(PROGRAMS "${CMAKE_SOURCE_DIR}/stacks/baycom-pr/scripts/baycom-pr-ctl"
        DESTINATION "${CMAKE_INSTALL_SBINDIR}")

set(_BAYCOM_PY_TOOLS
    baycom_ini_load.py
    baycom_validate_config.py
    baycom_preflight.py
    baycom_probe.py
    baycom_doctor.py
    baycom_axports.py
    baycom_serial_status.py
)
foreach(_py IN LISTS _BAYCOM_PY_TOOLS)
    install(PROGRAMS "${CMAKE_SOURCE_DIR}/stacks/baycom-pr/tools/${_py}"
            DESTINATION "${CMAKE_INSTALL_SBINDIR}")
endforeach()

install(FILES "${CMAKE_SOURCE_DIR}/stacks/baycom-pr/config/modems.ini"
        DESTINATION "${CMAKE_INSTALL_SYSCONFDIR}/baycom")

install(FILES "${CMAKE_SOURCE_DIR}/share/baycom/baycom-pr.pccom-ttyS0-only.ini.example"
        DESTINATION "${CMAKE_INSTALL_SYSCONFDIR}/baycom"
        RENAME "baycom-pr.ini.example")
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

add_custom_target(baycom_pr_test
    COMMAND bash "${CMAKE_SOURCE_DIR}/stacks/baycom-pr/scripts/test-all.sh"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    COMMENT "BayCom PR offline test-all"
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
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    COMMENT "max25d M25/1 smoke tests"
)

if(TARGET max25-terminal)
    add_custom_target(max25_terminal_test
        COMMAND bash "${CMAKE_SOURCE_DIR}/stacks/terminal/test-terminal.sh"
        DEPENDS max25-terminal
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        COMMENT "max25-terminal TCP probe"
    )
endif()


add_custom_target(max25_test
    DEPENDS max25_daemon_smoke
)

if(MAX25_BUILD_BAYCOM)
    add_dependencies(max25_test baycom_pr_test)
endif()

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
