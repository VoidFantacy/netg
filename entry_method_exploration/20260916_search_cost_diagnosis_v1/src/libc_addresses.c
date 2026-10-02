#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdio.h>
int main(){const char* names[]={"memmove","memcpy","memset","malloc","free"};for(int i=0;i<5;i++){void* p=dlsym(RTLD_DEFAULT,names[i]);Dl_info d;dladdr(p,&d);printf("%s %p %lx %s\n",names[i],p,(unsigned long)p-(unsigned long)d.dli_fbase,d.dli_fname);}return 0;}
