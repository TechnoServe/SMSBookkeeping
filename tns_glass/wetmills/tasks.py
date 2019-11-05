from celery.decorators import task
from datetime import datetime

@task(track_started=True)
def import_wetmills(task):  #pragma: no cover
    from .models import import_csv_wetmills
    from django.db import transaction

    transaction.enter_transaction_management()
    transaction.managed()

    try:
        task.task_id = import_wetmills.request.id
        task.import_log = "Started import at %s\n" % datetime.now()
        task.save()
        
        transaction.commit()

        wetmills = import_csv_wetmills(task.country, task.csv_file.file.name, task.created_by)

        task.log("Import finished at %s\n" % datetime.now())
        task.log("%d wetmill(s) added." % len(wetmills))

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
