/* Standard Workbench launcher for native regression support; no synthetic WBStartup. */
#include <proto/workbench.h>
int main(int argc,char **argv) {
    if (argc != 2) return 2;
    return OpenWorkbenchObjectA((STRPTR)argv[1],0) ? 0 : 3;
}
