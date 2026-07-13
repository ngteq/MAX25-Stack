cmake_minimum_required(VERSION 3.16)

if(NOT MAX25_BUILD_WEB)
    return()
endif()

set(_MAX25_WEB_SRC "${CMAKE_SOURCE_DIR}/stacks/web")

execute_process(
    COMMAND "${CMAKE_COMMAND}" -E chmod u+x
            "${_MAX25_WEB_SRC}/proxy/max25-ws-proxy.py"
            "${_MAX25_WEB_SRC}/scripts/dev-server.sh"
    ERROR_QUIET
)

install(PROGRAMS "${_MAX25_WEB_SRC}/proxy/max25-ws-proxy.py"
        DESTINATION "${CMAKE_INSTALL_BINDIR}"
        RENAME max25-ws-proxy)

install(FILES "${_MAX25_WEB_SRC}/share/web-proxy.ini.example"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25")

install(FILES "${CMAKE_SOURCE_DIR}/share/max25/max25-ws-proxy.service.example"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25")

install(DIRECTORY "${_MAX25_WEB_SRC}/share/reverse-proxy/"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/reverse-proxy")

install(PROGRAMS "${_MAX25_WEB_SRC}/scripts/dev-server.sh"
        DESTINATION "${CMAKE_INSTALL_DATADIR}/max25/web"
        RENAME max25-web-dev)

add_custom_target(max25_web_smoke
    COMMAND "${CMAKE_COMMAND}" -E env PYTHONPATH=
            python3 "${_MAX25_WEB_SRC}/proxy/test_ws_proxy.py"
    WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    COMMENT "MAX25 web proxy smoke test"
)
