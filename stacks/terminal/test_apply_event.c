/* Offline unit test: EVENT connected/disconnected → status.connected */
#include "max25_proto.h"

#include <stdio.h>
#include <string.h>

int main(void)
{
    max25_status_t st;

    memset(&st, 0, sizeof(st));
    if (max25_client_apply_event("EVENT connected", &st) != 1 || !st.connected) {
        fprintf(stderr, "FAIL: EVENT connected\n");
        return 1;
    }
    if (max25_client_apply_event("EVENT disconnected", &st) != 1 || st.connected) {
        fprintf(stderr, "FAIL: EVENT disconnected\n");
        return 1;
    }
    if (max25_client_apply_event("EVENT device=max25e0 serial=ready", &st) != 0) {
        fprintf(stderr, "FAIL: unrelated EVENT should be ignored\n");
        return 1;
    }
    if (max25_client_apply_event("OK", &st) != 0) {
        fprintf(stderr, "FAIL: non-EVENT\n");
        return 1;
    }
    puts("OK: apply_event");
    return 0;
}
