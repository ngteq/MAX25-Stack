add_executable(tnc2c-probe tnc2c-probe.c)
target_compile_options(tnc2c-probe PRIVATE -std=c99 -Wall -Wextra -O2)

add_executable(tnc2c-find tnc2c-find.c)
target_compile_options(tnc2c-find PRIVATE -std=c99 -Wall -Wextra -O2)

install(TARGETS tnc2c-probe tnc2c-find RUNTIME DESTINATION "${CMAKE_INSTALL_BINDIR}")
