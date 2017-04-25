from optparse import make_option
from django.core.management.base import BaseCommand
from mobileu.mobileu_elasticsearch import SchoolIndex


class Command(BaseCommand):
    help = 'Manages ElasticSearch indices.'
    option_list = BaseCommand.option_list + (
        make_option('-d', '--delete',
                    dest='delete_stale',
                    action='store_true',
                    default=False,
                    help='Deletes stale entries if operation is "update".'),
    )

    def handle(self, *args, **options):
        if args[0] == 'ensure_indices':
            self.stdout.write('Ensuring indices exist... ', ending='')
            try:
                SchoolIndex().ensure_index()
                self.stdout.write('done')
            except Exception as e:
                self.stdout.write('failed')
                self.stdout.write(e.message)
        elif args[0] == 'update':
            self.stdout.write('Updating indices... ', ending='')
            try:
                SchoolIndex().update_index(delete_stale=options['delete_stale'])
                self.stdout.write('done')
            except Exception as e:
                self.stdout.write('failed')
                self.stdout.write(e.message)
        elif args[0] == 'rebuild':
            self.stdout.write('Rebuilding indices... ', ending='')
            try:
                SchoolIndex().rebuild_index()
                self.stdout.write('done')
            except Exception as e:
                self.stdout.write('failed')
                self.stdout.write(e.message)

