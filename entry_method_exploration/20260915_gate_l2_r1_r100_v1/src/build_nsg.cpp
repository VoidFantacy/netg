#include "native_common.hpp"
int main(int argc,char** argv){try{
 require(argc==3,"build_nsg manifest output_dir");auto c=read_json(argv[1]);fs::path out=argv[2];
 require(!fs::exists(out/"complete.json"),"already complete; preserve graph");fs::create_directories(out);
 require(!fs::exists(out/"graph.nsg"),"uncommitted graph requires inspection");
 Fvecs base(c["paths"]["base_path"]);int metric=c["metric_id"];
 require(metric==0||metric==1,"unsupported metric");
 omp_set_dynamic(0);omp_set_num_threads(16);resources(out);
 std::vector<float> x(base.n*base.d);
 for(size_t i=0;i<base.n;++i)std::copy(base.row(i),base.row(i)+base.d,x.begin()+i*base.d);
 acsg::IndexACSGFlat idx(base.d,64,faiss::MetricType(metric));
 idx.nsg_R=64;idx.nsg_L=100;idx.nsg_C=512;idx.build_type=1;idx.verbose=true;
 auto t=Clock::now();idx.add(base.n,x.data());double build=seconds(t);
 require(idx.ntotal==base.n&&idx.metric_type==metric&&idx.is_built,"built identity");
 resources(out);t=Clock::now();idx.save((out/"graph.nsg").c_str());double save=seconds(t);
 write_json(out/"complete.json",{{"status","PASS"},{"n",base.n},{"d",base.d},{"metric_id",metric},{"R",64},{"L_build",100},{"C",512},{"build_seconds",build},{"save_seconds",save},{"threads",16},{"base_sha256",c["identities"]["base_path"]["sha256"]}});
 return 0;
 }catch(const std::exception& e){std::cerr<<e.what()<<std::endl;return 1;}}
