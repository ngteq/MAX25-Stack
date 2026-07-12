set(MAX25_TERMINAL_SRCS
    max25_terminal.c
    max25_proto.c
    max25_ui.c
)

add_executable(max25-terminal ${MAX25_TERMINAL_SRCS})
target_include_directories(max25-terminal PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")

find_package(Curses)
if(Curses_FOUND AND TARGET Curses::Curses)
    target_compile_definitions(max25-terminal PRIVATE MAX25_HAVE_NCURSES)
    target_link_libraries(max25-terminal PRIVATE Curses::Curses)
elseif(Curses_FOUND)
    target_compile_definitions(max25-terminal PRIVATE MAX25_HAVE_NCURSES)
    target_include_directories(max25-terminal PRIVATE ${CURSES_INCLUDE_DIR})
    target_link_libraries(max25-terminal PRIVATE ${CURSES_LIBRARIES})
elseif(UNIX AND NOT APPLE)
    target_compile_definitions(max25-terminal PRIVATE MAX25_HAVE_NCURSES)
    target_link_libraries(max25-terminal PRIVATE ncurses tinfo)
endif()

target_compile_options(max25-terminal PRIVATE -Wall -Wextra -std=c11 -O2)

add_custom_command(TARGET max25-terminal POST_BUILD
    COMMAND "${CMAKE_COMMAND}" -E rm -f "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/max25-client"
    COMMAND "${CMAKE_COMMAND}" -E create_symlink max25-terminal "${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/max25-client"
    COMMENT "max25-client -> max25-terminal"
)

install(TARGETS max25-terminal RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")

install(CODE "
    set(_dst \"\$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}/max25-client\")
    set(_src \"\$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}/max25-terminal\")
    if(EXISTS \"\${_dst}\")
        file(REMOVE \"\${_dst}\")
    endif()
    execute_process(COMMAND \"${CMAKE_COMMAND}\" -E create_symlink max25-terminal \"\${_dst}\")
")
