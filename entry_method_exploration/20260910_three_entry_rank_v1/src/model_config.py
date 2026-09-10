from common import RUN, read


def method(dataset, model, L=128, exact=False):
    inp=RUN/'inputs'/dataset
    size=read(inp/'prepared.json')['H']
    return {'family':model['family'],'model_name':model['name'],'lambda':model.get('lambda'),
        'name':model['name']+('_exact' if exact else '_hnsw')+f'_L{L}',
        'L':L,'seed':20260828,'hnsw_seed':20260828,'hub_count':size,'k':3,
        'W':model['W'],'mapping':str(inp/'hub_ids.i32'),'tie_ids':str(inp/'hub_ids.i32'),
        'slot_labels':False,'exact':exact,'legacy_heap_order':False,'canonical_entry_order':True}


def baseline(dataset):
    return {'name':'fast20k_3','family':'fast20k_3','W':str(RUN/'inputs'/dataset/'P0.f32')}
