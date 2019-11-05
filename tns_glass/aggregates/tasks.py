from celery.decorators import task
from datetime import datetime

@task(track_started=True)
def finalize_season(task):  #pragma: no cover
    from .models import SeasonAggregate
    from django.db import transaction

    transaction.enter_transaction_management()
    transaction.managed()

    try:
        task.task_id = finalize_season.request.id
        task.task_log = "Started finalizing season at %s\n" % datetime.now()
        task.save()
        
        transaction.commit()

        report_count = SeasonAggregate.calculate_for_season(task.season)

        task.log("Season finished at %s\n" % datetime.now())
        task.log("%d finalized reports(s) included in season." % report_count)

        transaction.commit()

    except Exception as e:
        import traceback
        traceback.print_exc()
        
        task.log("Error: %s" % e)
        transaction.commit()

        raise e

    finally:
        transaction.leave_transaction_management()
    
    return task
