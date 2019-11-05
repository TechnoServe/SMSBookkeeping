from celery.task import task
import datetime

from celery.contrib import rdb

@task(track_started=True)
def approve_submission(submission, clazz): # pragma: no cover
    hour_later = submission.created + datetime.timedelta(minutes=59)
    now = datetime.datetime.now()
    
    if now >= hour_later and not clazz.all.filter(created__gt=submission.created,
                                                  created__lt=hour_later,
                                                  accountant=submission.accountant,
                                                  wetmill=submission.wetmill):
        # then approve it
        submission.active = True
        submission.is_active = True
        submission.save()

        submission.confirm()

        print "[%d] %s : confirmed" % (submission.pk, submission)
    else:
        print "[%d] %s : not confirmed" % (submission.pk, submission)
