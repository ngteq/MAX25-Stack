cmake_minimum_required(VERSION 3.16)
project(MainAX25Stack VERSION 1.0.0 LANGUAGES C)

include(GNUInstallDirs)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

option(MAX25_BUILD_TNCS "Build stacks/tncs tools" ON)
option(MAX25_BUILD_BAYCOM "Build stacks/baycom-pr tools" ON)
option(MAX25_BUILD_CRDOP "Build stacks/crdop (crdopc)" ON)
option(MAX25_BUILD_TERMINAL "Build max25-terminal / max25-client" ON)
option(MAX25_BUILD_DAEMON "Install max25d" ON)

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

if(MAX25_BUILD_DAEMON)
    execute_process(
        COMMAND "${CMAKE_COMMAND}" -E chmod u+x "${CMAKE_SOURCE_DIR}/stacks/daemon/max25d"
        ERROR_QUIET
    )
    install(PROGRAMS "${CMAKE_SOURCE_DIR}/stacks/daemon/max25d"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/kiss_bridge.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/device_backends.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/banlist.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    install(FILES "${CMAKE_SOURCE_DIR}/stacks/daemon/paths.py"
            DESTINATION "${CMAKE_INSTALL_BINDIR}")
    set(_MAX25_STACK_PROGRAMS
        stacks/tncs/load-serial-env.sh
        stacks/tncs/tnc2c-boot-wait.sh
        stacks/tncs/tnc2c-host-reset.sh
        stacks/tncs/pktnc2-boot-wait.sh
        stacks/crdop/scripts/crdopc
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

install(PROGRAMS "${CMAKE_SOURCE_DIR}/scripts/max25-ctl"
        DESTINATION "${CMAKE_INSTALL_BINDIR}")

install(FILES
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.ini.host.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.full-station.ini.example"
    "${CMAKE_SOURCE_DIR}/share/max25/max25d.dual-baycom.ini.example"
    DESTINATION "${CMAKE_INSTALL_DATADIR}/max25"
)

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
    DEPENDS max25_daemon_smoke baycom_pr_test
)

if(TARGET crdop_smoke)
    add_dependencies(max25_test crdop_smoke)
endif()

if(TARGET max25-terminal)
    add_dependencies(max25_test max25_terminal_test)
endif()

message(STATUS "MainAX25-Stack → ${CMAKE_BINARY_DIR}/bin (install prefix: ${CMAKE_INSTALL_PREFIX})")
