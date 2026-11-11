struct Model {
 struct TreeNode {int f,l,r;double t,v;bool leaf;};
 int count=0;double bias=0,threshold=0;bool off=true;std::string type;
 std::vector<double>coef;std::vector<std::vector<TreeNode>>trees;
 Model()=default;
 explicit Model(const json&j):count(j.at("feature_count")),bias(j.at("bias")),threshold(j.at("threshold")),off(j.at("gate_all_off")),type(j.at("type")){
  if(type=="ridge")coef=j.at("coef").get<std::vector<double>>();
  else for(auto tree:j.at("trees")){std::vector<TreeNode>v;for(auto n:tree)v.push_back({n.at("f"),n.at("l"),n.at("r"),n.at("t"),n.at("v"),n.at("leaf")});trees.push_back(std::move(v));}
 }
 double predict(const float*x)const{double s=bias;if(type=="ridge"){for(int j=0;j<count;++j)s+=coef[j]*double(x[j]);}
  else for(auto&tree:trees){int i=0;while(!tree[i].leaf)i=x[tree[i].f]<=tree[i].t?tree[i].l:tree[i].r;s+=tree[i].v;}return s;}
};
