from common import *
assert read(O/'state.json')['status']=='PREPARED_LABELS_PENDING';check(O/'reviews/before_labels.json')
for ds in DS:run_job('labels_'+ds,O/'inputs'/ds/'config.json',O/'results'/('labels_'+ds),2048*56+96)
dump(O/'state.json',dict(status='LABELS_COMPLETE_VERIFY_PENDING',training_runs=0,validation_read=False,heldout_read=False))
