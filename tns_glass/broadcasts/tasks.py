from datetime import datetime
from celery.task import task
from django.conf import settings
from broadcasts.models import *
import redis

@task(track_started=True)
def send_broadcasts(): #pragma: no cover
    """
    Checks all our broadcasts trying to see if any of them need to be sent
    """
    # we use redis to acquire a global lock based on our settings key
    r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

    now = datetime.now()
    for broadcast in Broadcast.get_pending(now):
        # try to acquire a lock, at most it will last 60 seconds
        with r.lock('send_broadcast_%d' % broadcast.pk, timeout=300):
            # send each broadcast
            broadcast.send()
