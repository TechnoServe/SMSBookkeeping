from celery.contrib.methods import task
from dashboard.models import NYCherryPrice
from seasons.models import Season
from datetime import datetime


@task(track_started=True, name='dashboard.tasks.save_nyc_price')
def save_nyc_price(): # pragma: no cover
    # already one for today?  don't bother
    today = datetime.today()
    if not NYCherryPrice.objects.filter(date=today):
        ny_price = NYCherryPrice.update_nyc_price()

        if ny_price:
            print "NY Price updated to: %s" % ny_price.price
        else:
            print "Error fetching NY Price, will retry"


@task(track_started=True, name='dashboard.tasks.update_exchange_rate')
def update_exchange_rate():
    today = datetime.today()
    if not Season.objects.filter(modified_on__startswith=today.date(), created_on__year=today.year): #Only change exchange rates for seasons created this year.  Needs to use the Active bit.
        for season in Season.objects.filter(created_on__year=today.year):
            print 'Season chosen: %s' % season
            rate = season.update_exchange_rate()
            if rate:
                print 'Rate for %s has been updated to %s ' % (season.country.currency.currency_code, rate)
            else:
                print 'Error fetching exchange rate for %s ' % season.country.currency.currency_code
