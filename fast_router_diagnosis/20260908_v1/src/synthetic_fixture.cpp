// Entirely synthetic, tiny end-to-end acceptance of serialization and result schema.
#define main diagnostic_main
#include "fast_router_diagnosis.cpp"
#undef main

int main(int argc,char** argv) {
    try {
        require(argc==2,"usage: synthetic_fixture NEW_DIR");
        fs::path root=fs::absolute(argv[1]);
        require(!fs::exists(root),"synthetic directory already exists");
        require(fs::create_directory(root),"cannot create synthetic directory");
        constexpr size_t n=192,d=8,h=32,nq=20,p=12,degree=12,gtk=100;
        acsg::IndexACSGFlat index(d,degree,faiss::METRIC_INNER_PRODUCT);
        std::vector<float> base(n*d),query(nq*d);
        for(size_t i=0;i<base.size();++i) base[i]=std::sin(float(i+1)*.371f);
        for(size_t i=0;i<query.size();++i) query[i]=std::sin(float(i+1)*.317f+.731f);
        index.storage->add(n,base.data());index.ntotal=n;index.is_built=true;index.is_trained=true;
        index.acsg.ntotal=n;index.acsg.is_built=true;index.acsg.enterpoint=0;
        index.acsg.pheromone.assign(n,1);index.acsg.weight.assign(n,1);
        index.acsg.final_graph=std::make_shared<acsg::Graph<int32_t>>(n,degree);
        for(size_t i=0;i<n;++i) for(size_t j=0;j<degree;++j) index.acsg.final_graph->at(i,j)=(i+j*13+1)%n;
        index.saveACPG((root/"synthetic_index.bin").c_str());
        std::vector<int32_t> hubs(h);std::iota(hubs.begin(),hubs.end(),0);
        std::vector<int64_t> rows(nq);std::iota(rows.begin(),rows.end(),0);
        std::vector<float> raw(base.begin(),base.begin()+h*d),proto=raw;
        for(size_t j=0;j<h;++j) normalize(proto.data()+j*d,d);
        std::vector<int64_t> gt(nq*gtk);
        std::unique_ptr<faiss::DistanceComputer> dc(acsg::storage_distance_computer(index.storage));
        for(size_t q=0;q<nq;++q) {
            dc->set_query(query.data()+q*d);
            std::vector<std::pair<float,int32_t>> ranked(n);
            for(size_t j=0;j<n;++j) ranked[j]={(*dc)(j),static_cast<int32_t>(j)};
            std::sort(ranked.begin(),ranked.end());
            for(size_t j=0;j<gtk;++j) gt[q*gtk+j]=ranked[j].second;
        }
        write_raw(root/"queries.f32",query);write_raw(root/"gt.i64",gt);write_raw(root/"row_ids.i64",rows);
        write_raw(root/"hub_ids.i32",hubs);write_raw(root/"raw_hubs.f32",raw);write_raw(root/"prototypes.f32",proto);
        json c={{"dim",d},{"index_path",(root/"synthetic_index.bin").string()},{"queries_file",(root/"queries.f32").string()},
            {"gt_file",(root/"gt.i64").string()},{"row_ids",(root/"row_ids.i64").string()},{"hub_ids",(root/"hub_ids.i32").string()},
            {"raw_hubs",(root/"raw_hubs.f32").string()},{"prototypes",(root/"prototypes.f32").string()},
            {"pilot_count",p},{"gt_k",gtk},{"L",{64,128}},{"threads",2}};
        write_json(root/"config.json",c);
        run(c,root/"result",2,false);
        const size_t v=91;
        size_t mask_checks=0;
        for(int l:{64,128}) for(auto prefix:{"all_single","pilot"}) {
            size_t r=std::string(prefix)=="all_single"?nq:p,col=std::string(prefix)=="all_single"?h:v;
            fs::path dir=root/"result"/("L"+std::to_string(l));
            auto ids=read_raw<int32_t>((dir/(std::string(prefix)+".ids.i32")).string());
            auto count=read_raw<uint8_t>((dir/(std::string(prefix)+".hitcount.u8")).string());
            auto masks=read_raw<uint16_t>((dir/(std::string(prefix)+".hitmask.u16")).string());
            auto ndc=read_raw<uint32_t>((dir/(std::string(prefix)+".ndc.u32")).string());
            require(ids.size()==r*col*K && count.size()==r*col && masks.size()==r*col && ndc.size()==r*col,"serialized shape failure");
            for(size_t i=0;i<r*col;++i) {
                std::array<int32_t,K> row;std::copy(ids.begin()+i*K,ids.begin()+(i+1)*K,row.begin());
                uint16_t m=hitmask(row,gt.data()+(i/col)*gtk);
                require(m==masks[i] && __builtin_popcount(static_cast<unsigned>(m))==count[i] && ndc[i]>=1,"serialized hit mask/count/NDC failure");
                ++mask_checks;
            }
        }
        auto entries=read_raw<int32_t>((root/"result/pilot.entry_local.i32").string());
        require(entries.size()==p*v*3,"serialized entry shape failure");
        std::cout<<json({{"status","PASS"},{"kind","synthetic_end_to_end_only"},{"serialized_mask_checks",mask_checks},{"variants",v}}).dump()<<std::endl;
        return 0;
    } catch(const std::exception& e) {std::cerr<<"SYNTHETIC ERROR: "<<e.what()<<std::endl;return 1;}
}
