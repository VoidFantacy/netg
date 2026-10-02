#include <string>
#include <stdexcept>
#include <iostream>
#include <vector>
#include <cerrno>
#include <sys/wait.h>
#include <unistd.h>
static void require(bool ok,const char*message){if(!ok)throw std::runtime_error(message);}
static std::string sha256_bytes(const void* raw,size_t bytes){
 int in[2],out[2];require(pipe(in)==0&&pipe(out)==0,"sha pipes");pid_t pid=fork();require(pid>=0,"sha fork");
 if(pid==0){dup2(in[0],STDIN_FILENO);dup2(out[1],STDOUT_FILENO);close(in[0]);close(in[1]);close(out[0]);close(out[1]);execl("/usr/bin/sha256sum","sha256sum",(char*)nullptr);_exit(127);}
 close(in[0]);close(out[1]);const char*p=static_cast<const char*>(raw);size_t done=0;
 while(done<bytes){ssize_t n=write(in[1],p+done,bytes-done);if(n<0&&errno==EINTR)continue;require(n>0,"sha write");done+=size_t(n);}
 close(in[1]);std::string value;char buf[256];for(;;){ssize_t n=read(out[0],buf,sizeof(buf));if(n<0&&errno==EINTR)continue;require(n>=0,"sha read");if(!n)break;value.append(buf,size_t(n));}
 close(out[0]);int status;require(waitpid(pid,&status,0)==pid&&WIFEXITED(status)&&WEXITSTATUS(status)==0,"sha child exit");
 require(value.size()>=64,"sha length");value.resize(64);require(value.find_first_not_of("0123456789abcdef")==std::string::npos,"sha format");return value;
}

int main(){try{
std::string a="abc";std::vector<unsigned char>b(4096);for(size_t i=0;i<b.size();++i)b[i]=i%256;
std::cout<<sha256_bytes(nullptr,0)<<"\n"<<sha256_bytes(a.data(),a.size())<<"\n"<<sha256_bytes(b.data(),b.size())<<"\n";
return 0;}catch(const std::exception&e){std::cerr<<e.what()<<std::endl;return 1;}}
