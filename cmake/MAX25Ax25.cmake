# MAX25Ax25.cmake — native AX.25 codec only (no upstream bundle).
#
# libax25 / ax25-tools / ax25-apps tarballs under third_party/ax25/ are study
# reference material. max25d ships stacks/daemon/ax25_codec.py + kiss_bridge.py.
# Optional host tools (listen, call, kissattach): install distro ax25-apps /
# ax25-tools or run scripts/build-ax25-deps.sh manually (deprecated for MAX25).

option(MAX25_BUNDLE_AX25
       "DEPRECATED: build libax25/ax25-tools/ax25-apps from third_party/ax25 tarballs"
       OFF)

if(MAX25_BUNDLE_AX25)
    message(WARNING
        "MAX25_BUNDLE_AX25=ON is deprecated. "
        "Use distro ax25-apps/ax25-tools or scripts/build-ax25-deps.sh manually. "
        "max25d uses native ax25_codec.py — no libax25 link required.")
endif()

message(STATUS "AX.25: native ax25_codec.py (third_party/ax25 study reference only)")
