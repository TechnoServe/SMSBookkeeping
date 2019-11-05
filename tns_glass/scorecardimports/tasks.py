from celery.decorators import task
from datetime import datetime
import StringIO

@task(track_started=True)
def import_scorecards(task):  #pragma: no cover
    from .models import import_season_scorecards
    from django.db import transaction

    transaction.enter_transaction_management()
    transaction.managed()

    log = StringIO.StringIO()

    try:
        task.task_id = import_scorecards.request.id
        task.import_log = "Started import at %s\n\n" % datetime.now()
        task.save()

        transaction.commit()

        reports = import_season_scorecards(task.season, task.csv_file.file.name, task.created_by, log)

        task.log(log.getvalue())
        task.log("Import finished at %s\n" % datetime.now())
        task.log("%d scorecard(s) added." % len(reports))

        transaction.commit()

    except Exception as e:
        import traceback
        traceback.print_exc(e)

        task.log("\nError: %s\n" % e)
        task.log(log.getvalue())
        transaction.commit()

        raise e

    finally:
        transaction.leave_transaction_management()
    
    return task
