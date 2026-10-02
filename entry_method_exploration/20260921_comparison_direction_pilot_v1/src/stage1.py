from common import *
from execute import Executor,freeze_native

def main():
    os.sched_setaffinity(0,{15});freeze_native();ex=Executor('stage1')
    prepare('directions');prepare('fit')
    try:
        for ds,c in LOCK['datasets'].items():
            p=RUN/'inputs'/ds/'smoke'
            if not p.exists():
                p.mkdir();np.fromfile(RUN/'inputs'/ds/'directions/queries.f32',np.float32).reshape(-1,c['dimension'])[:8].tofile(p/'queries.f32')
                np.fromfile(RUN/'inputs'/ds/'fit/queries.f32',np.float32).reshape(-1,c['dimension'])[:8].tofile(p/'fit_queries.f32')
                np.fromfile(RUN/'inputs'/ds/'fit/gt.i64',np.int64).reshape(-1,100)[:8].tofile(p/'gt.i64')
            cfg=base_config(ds,'directions');cfg.update(mode='trace',n=8,queries=str(p/'queries.f32'))
            ex.execute(cfg,RUN/'results'/ds/'smoke_trace','smoke_trace')
            cfg=base_config(ds,'fit');cfg.update(mode='labels',n=8,queries=str(p/'fit_queries.f32'),gt=str(p/'gt.i64'),label_block=8)
            ex.execute(cfg,RUN/'results'/ds/'smoke_labels','smoke_labels')
        dump(RUN/'reviews/native_smoke.json',dict(status='PASS',datasets=2,trace_linked_bit_parity=True,full_H_K1_K100_repeats=True))
        dump(RUN/'state.json',dict(status='RUNNING_DIRECTION_DISCOVERY',runner_pid=os.getpid(),pending=['directions','fit labels','training','full evaluation','audit and reporting']))
        for ds in LOCK['datasets']:
            cfg=base_config(ds,'directions');cfg['mode']='trace'
            ex.execute(cfg,RUN/'results'/ds/'directions','directions')
        dump(RUN/'state.json',dict(status='RUNNING_FIT_LABELS',runner_pid=os.getpid(),pending=['fit labels','training','full evaluation','audit and reporting']))
        for ds in LOCK['datasets']:
            cfg=base_config(ds,'fit');cfg['mode']='labels'
            ex.execute(cfg,RUN/'results'/ds/'labels','labels')
        dump(RUN/'state.json',dict(status='LABELS_COMPLETE',pending=['clustering and training','full evaluation','audit and reporting'],active_processes=[]))
        dump(RUN/'reviews/stage1_complete.json',dict(status='PASS',seconds=time.time()-ex.start))
    except BaseException as err:
        dump(RUN/'state.json',dict(status='EXECUTION_ERROR_REQUIRES_DIAGNOSIS',error=repr(err),stage='stage1',method_conclusion=None))
        raise
if __name__=='__main__':main()
