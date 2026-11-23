/* Diagnostic for the pinned AROS -nix CRT; operates only in its own drawer. */
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/stat.h>
#include <dirent.h>
static void result(const char *op,int rc) { int e=errno; printf("%s: rc=%d errno=%d %s\n",op,rc,e,strerror(e)); }
int main(void) {
 const char *dir="/AROS/LCfileProbe"; int fd,i; char a[256],b[256];
 result("mkdir",mkdir(dir,0777));
 snprintf(a,sizeof a,"%s/stage",dir); snprintf(b,sizeof b,"%s/dest",dir);
 for(i=0;i<3;i++) {
  unlink(a); errno=0; fd=open(a,O_WRONLY|O_CREAT|O_EXCL,0666);result("open stage",fd);
  errno=0;result("write stage",write(fd,"hello",5)); errno=0;result("fsync stage",fsync(fd));
  errno=0;result("close stage",close(fd));errno=0;result("rename stage over dest",rename(a,b));
 }
 errno=0;fd=open(b,O_WRONLY|O_APPEND);result("open append",fd);errno=0;result("ftruncate zero",ftruncate(fd,0));result("close",close(fd));
 snprintf(a,sizeof a,"%s/za\xc5\xbc\xc3\xb3\xc5\x82\xc4\x87.png",dir);
 errno=0;result("UTF8 copy",0);FILE *in=fopen("/AROS/LCinput/Fixtures/sample.png","rb"),*out=fopen(a,"wb");
 if(in&&out){int c;while((c=fgetc(in))!=EOF)fputc(c,out);}if(in)fclose(in);if(out)fclose(out);
 DIR *d=opendir("/AROS/LCinput/Fixtures");struct dirent *entry;
 if(d){while((entry=readdir(d))){const unsigned char *s=(void*)entry->d_name;printf("name hex:");while(*s)printf("%02x",*s++);puts("");}closedir(d);}
 return 0;
}
