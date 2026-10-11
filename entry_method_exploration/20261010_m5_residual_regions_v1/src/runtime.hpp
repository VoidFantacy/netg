#pragma once
#include "native.hpp"
#include <cstdint>
namespace exp172::m5 {
enum class Mode {POST, RESCORE_ONLY, EMPTY};
struct PostStats{uint64_t lookups=0,probes=0,fallbacks=0,row_reads=0,candidates=0,dots=0,commits=0,nonfinite_failures=0;};
struct Posting {
 uint32_t H=0,b=0,hash_n=0,base_n=0,pairs=0;bool empty=true,global=false;
 std::vector<int32_t> labels,targets,hash_keys,hash_slots,sorted_labels,sorted_slots,global_ids;std::vector<uint8_t>counts;
 struct Record{faiss::idx_t id;float distance;uint32_t priority;bool padding;};
 std::array<int32_t,24>candidate{};std::array<Record,124>records{},heap{};
 static bool better(const Record&a,const Record&b){if(a.padding!=b.padding)return !a.padding;if(a.distance<b.distance)return true;if(b.distance<a.distance)return false;return a.priority<b.priority;}
 explicit Posting(uint32_t actual_base_n):base_n(actual_base_n),empty(true),global(true){require(base_n>0,"dynamic candidate merger static base domain");global_ids.reserve(24);require(resident_bytes()<=8192,"standalone merger complete scratch reserve");}
 explicit Posting(const std::string&path,bool is_global=false,uint32_t global_base_n=0):global(is_global){
  if(global){require(global_base_n>0,"global static base-domain binding required");base_n=global_base_n;global_ids=read_raw<int32_t>(path);require(global_ids.size()<=24,"global candidate budget");require(std::set<int32_t>(global_ids.begin(),global_ids.end()).size()==global_ids.size(),"global unique IDs");for(auto id:global_ids)require(id>=0&&uint32_t(id)<base_n,"global IDs in frozen base");empty=global_ids.empty();require(resident_bytes()<=128*1024,"global resident+scratch budget");return;}
  auto bytes=read_raw<uint8_t>(path);require(bytes.size()>=40&&!memcmp(bytes.data(),"M5POST1\0",8),"posting format");uint32_t header[8];memcpy(header,bytes.data()+8,32);require(header[0]==1,"posting version");H=header[1];b=header[2];hash_n=header[3];pairs=header[4];base_n=header[5];require(H>0&&b==8&&hash_n>=2*H&&(hash_n&(hash_n-1))==0,"posting capacities");
  require(base_n>0&&(!global_base_n||base_n==global_base_n),"posting actual static base identity");
  size_t offset=40;auto take32=[&](std::vector<int32_t>&a,size_t n){require(n<=(bytes.size()-offset)/4,"posting offset");a.resize(n);memcpy(a.data(),bytes.data()+offset,n*4);offset+=n*4;};
  take32(labels,H);require(H<=bytes.size()-offset,"count offset");counts.assign(bytes.begin()+offset,bytes.begin()+offset+H);offset+=H;take32(targets,size_t(H)*8);take32(hash_keys,hash_n);take32(hash_slots,hash_n);take32(sorted_labels,H);take32(sorted_slots,H);require(offset==bytes.size()&&std::is_sorted(sorted_labels.begin(),sorted_labels.end()),"posting complete layout");
  require(std::set<int32_t>(labels.begin(),labels.end()).size()==H,"unique actual labels");for(auto id:labels)require(id>=0&&uint32_t(id)<base_n,"actual label static domain");
  size_t occupied=0;for(size_t i=0;i<hash_n;++i){if(hash_keys[i]==-1)require(hash_slots[i]==-1,"empty hash slot");else{const auto slot=hash_slots[i];require(slot>=0&&uint32_t(slot)<H&&hash_keys[i]==labels[slot],"every hash key/slot access bounded");++occupied;}}require(occupied==H,"complete hash occupancy");
  uint32_t total=0;for(size_t j=0;j<H;++j){require(counts[j]<=8,"row capacity");std::set<int32_t>seen;for(size_t t=0;t<8;++t){auto id=targets[j*8+t];if(t<counts[j])require(id>=0&&uint32_t(id)<base_n&&seen.insert(id).second,"posting ID/domain/unique");else require(id==-1,"unused posting padding");}total+=counts[j];}require(total==pairs,"pair count");empty=pairs==0;
  for(size_t i=0;i<H;++i){require(sorted_slots[i]>=0&&uint32_t(sorted_slots[i])<H&&labels[sorted_slots[i]]==sorted_labels[i],"fallback exact map");require(lookup(labels[i],nullptr)==int(i),"all actual-label lookup paths");}
  require(resident_bytes()<=128*1024,"posting resident+scratch budget");
 }
 size_t resident_bytes()const{size_t allocs=0;for(auto n:{labels.capacity(),targets.capacity(),hash_keys.capacity(),hash_slots.capacity(),sorted_labels.capacity(),sorted_slots.capacity(),global_ids.capacity(),counts.capacity()})allocs+=n>0;return sizeof(*this)+4*(labels.capacity()+targets.capacity()+hash_keys.capacity()+hash_slots.capacity()+sorted_labels.capacity()+sorted_slots.capacity()+global_ids.capacity())+counts.capacity()+64*allocs;}
 int lookup(int32_t key,PostStats*s){if(s)++s->lookups;uint32_t pos=(uint32_t(key)*2654435761u)&(hash_n-1);for(int probe=0;probe<16;++probe){if(s)++s->probes;int32_t found=hash_keys[pos];if(found==key)return hash_slots[pos];if(found==-1)return -1;pos=(pos+1)&(hash_n-1);}if(s)++s->fallbacks;auto it=std::lower_bound(sorted_labels.begin(),sorted_labels.end(),key);if(it==sorted_labels.end()||*it!=key)return -1;return sorted_slots[it-sorted_labels.begin()];}
 int plan(const std::array<int32_t,3>&route,const faiss::idx_t*R,int K,PostStats*s){
  int n=0;auto append=[&](int32_t id){for(int j=0;j<K;++j)if(R[j]==id)return;for(int j=0;j<n;++j)if(candidate[j]==id)return;require(n<24,"max unique candidates");candidate[n++]=id;};
  if(global){for(auto id:global_ids)append(id);}else{for(auto label:route){int slot=lookup(label,s);if(slot<0)return -1;if(s)++s->row_reads;for(int j=0;j<counts[slot];++j)append(targets[slot*8+j]);}}
  if(s)s->candidates+=n;return n;
 }
 void apply(faiss::DistanceComputer&dc,const std::array<int32_t,3>&route,int K,faiss::idx_t*I,float*D,Mode mode,PostStats*s=nullptr){
  require(K==1||K==100,"real K1/K100");if(mode==Mode::EMPTY||empty)return;
  int nc=plan(route,I,K,s);if(nc<=0)return;
  for(int j=0;j<K;++j){records[j]={I[j],std::numeric_limits<float>::max(),uint32_t(j),I[j]<0};if(I[j]>=0){records[j].distance=dc(I[j]);if(s)++s->dots;if(!std::isfinite(records[j].distance)){if(s)++s->nonfinite_failures;return;}}}
  if(mode==Mode::POST)for(int j=0;j<nc;++j){float value=dc(candidate[j]);if(s)++s->dots;if(!std::isfinite(value)){if(s)++s->nonfinite_failures;return;}records[K+j]={candidate[j],value,uint32_t(K+j),false};}
  std::copy(records.begin(),records.begin()+K,heap.begin());std::make_heap(heap.begin(),heap.begin()+K,better);
  if(mode==Mode::POST)for(int j=0;j<nc;++j){const auto&incoming=records[K+j];if(heap[0].padding||incoming.distance<heap[0].distance){std::pop_heap(heap.begin(),heap.begin()+K,better);heap[K-1]=incoming;std::push_heap(heap.begin(),heap.begin()+K,better);}}
  std::sort(heap.begin(),heap.begin()+K,better);for(int j=0;j<K;++j){I[j]=heap[j].padding?-1:heap[j].id;D[j]=heap[j].padding?std::numeric_limits<float>::max():heap[j].distance;}if(s)++s->commits;
 }
};
}
