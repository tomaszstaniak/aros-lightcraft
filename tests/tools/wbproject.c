/* Diagnostic support: create a real Workbench project icon with an owned default tool. */
#include <stdio.h>
#include <workbench/workbench.h>
#include <proto/icon.h>
int main(int argc, char **argv) {
    if (argc != 3) return 2;
    struct DiskObject *object = GetDefDiskObject(WBPROJECT);
    if (!object) return 3;
    STRPTR previous = object->do_DefaultTool;
    object->do_DefaultTool = (STRPTR)argv[2];
    object->do_StackSize = 16777216;
    int ok = PutDiskObject((CONST_STRPTR)argv[1], object);
    object->do_DefaultTool = previous;
    FreeDiskObject(object);
    return ok ? 0 : 4;
}
