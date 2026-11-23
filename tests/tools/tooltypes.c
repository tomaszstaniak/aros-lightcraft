/* Diagnostic support only: update a copied program icon, preserving its artwork/stack. */
#include <stdio.h>
#include <workbench/workbench.h>
#include <proto/icon.h>
int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr,"usage: SetToolTypes PROGRAM [KEY=VALUE ...]\n"); return 2; }
    struct DiskObject *icon = GetDiskObject((CONST_STRPTR)argv[1]);
    if (!icon) return 3;
    STRPTR *owned = icon->do_ToolTypes;
    /* PutDiskObject borrows these strings for this call. FreeDiskObject must only free owned data. */
    icon->do_ToolTypes = (STRPTR *)(argv + 2);
    int ok = PutDiskObject((CONST_STRPTR)argv[1], icon);
    icon->do_ToolTypes = owned;
    FreeDiskObject(icon);
    return ok ? 0 : 4;
}
