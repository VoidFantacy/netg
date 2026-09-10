#include <metis.h>
#include <stdio.h>
int main(void) {
    _Static_assert(sizeof(idx_t) == 8, "METIS must use 64-bit indices");
    idx_t n=6, constraints=1, parts=2, cut=0;
    idx_t offsets[]={0,2,4,7,10,12,14};
    idx_t edges[]={1,2,0,2,0,1,3,2,4,5,3,5,3,4};
    idx_t output[6], options[METIS_NOPTIONS];
    METIS_SetDefaultOptions(options);
    options[METIS_OPTION_SEED]=2026090711;
    options[METIS_OPTION_UFACTOR]=200;
    int status=METIS_PartGraphKway(&n,&constraints,offsets,edges,0,0,0,
                                  &parts,0,0,options,&cut,output);
    if (status!=METIS_OK) return 1;
    int counts[2]={0,0};
    for (int i=0;i<6;i++) { if(output[i]<0||output[i]>=2) return 2; counts[output[i]]++; }
    if(counts[0]!=3||counts[1]!=3||cut!=1) return 3;
    printf("{\"status\":\"PASS\",\"idx_bits\":%zu,\"real_bits\":%zu,\"cut\":%lld,\"nodes\":6}\n",
           sizeof(idx_t)*8,sizeof(real_t)*8,(long long)cut);
    return 0;
}
