#pragma once
#include <unordered_map>
struct ComparisonRecorder {
 std::unordered_map<uint64_t,uint8_t> pairs;
 uint64_t total_calls=0,valid_calls=0;
 void clear(){pairs.clear();total_calls=valid_calls=0;}
 void compare(int a,float da,int b,float db,uint8_t kind){
  ++total_calls;if(a<0||b<0||a==b)return;++valid_calls;
  require(std::isfinite(da)&&std::isfinite(db),"finite comparison");
  if(a>b){std::swap(a,b);std::swap(da,db);}
  uint8_t sign=da<db?1:da>db?2:4;
  uint64_t key=(uint64_t(uint32_t(a))<<32)|uint32_t(b);
  pairs[key]|=uint8_t(sign|(kind<<3));
 }
 std::vector<std::pair<uint64_t,uint8_t>> sorted()const{
  std::vector<std::pair<uint64_t,uint8_t>> out(pairs.begin(),pairs.end());std::sort(out.begin(),out.end());return out;
 }
};
inline int traced_insert_into_pool_live(acsg::Neighbor* addr,int capacity,int live_count,acsg::Neighbor nn,ComparisonRecorder& recorder){
 int left=0,right=capacity-1;
 recorder.compare(addr[left].id,addr[left].distance,nn.id,nn.distance,16);
 if(addr[left].distance>nn.distance){std::memmove(addr+1,addr,live_count*sizeof(acsg::Neighbor));addr[0]=nn;return 0;}
 recorder.compare(addr[right].id,addr[right].distance,nn.id,nn.distance,16);
 if(addr[right].distance<nn.distance){addr[capacity]=nn;return capacity;}
 while(left<right-1){int mid=(left+right)/2;recorder.compare(addr[mid].id,addr[mid].distance,nn.id,nn.distance,4);if(addr[mid].distance>nn.distance)right=mid;else left=mid;}
 while(left>0){recorder.compare(addr[left].id,addr[left].distance,nn.id,nn.distance,8);if(addr[left].distance<nn.distance)break;if(addr[left].id==nn.id)return capacity+1;--left;}
 if(addr[left].id==nn.id||addr[right].id==nn.id)return capacity+1;
 std::memmove(addr+right+1,addr+right,std::max(0,live_count-right)*sizeof(acsg::Neighbor));addr[right]=nn;return right;
}
