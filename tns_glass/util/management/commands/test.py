from django.core.management.commands import test
from south.management.commands import patch_for_test_db_setup
from django.test.utils import get_runner
from django.conf import settings

TestRunner = get_runner(settings)

if hasattr(TestRunner, 'options'):
    extra_options = TestRunner.options
else:
    extra_options = []

class Command(test.Command):
    option_list = test.Command.option_list + tuple(extra_options)

    def handle(self, *args, **kwargs):
        patch_for_test_db_setup()
        super(Command, self).handle(*args, **kwargs)
