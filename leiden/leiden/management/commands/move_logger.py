import logging

from django.core.management.base import BaseCommand

from acacia.meetnet.models import Datalogger, Well
import pytz
from dateutil.parser import parse

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Move an existing datalogger to another screen'
    
    def add_arguments(self, parser):
        parser.add_argument('logger')
        parser.add_argument('screen')
        parser.add_argument('start')
        parser.add_argument('depth',nargs='?',type=float)

    def handle(self, *args, **options):
        datalogger = Datalogger.objects.get(serial=options['logger'])
        well_name,screen_nr = options['screen'].split('/')
        screen = Well.objects.get(name__iexact=well_name).screen_set.get(nr=screen_nr)
        curpos = datalogger.loggerpos_set.latest('start_date')
        depth = options['depth']
        if depth is None: 
            depth = curpos.depth
        tz = pytz.timezone('CET')
        newpos = datalogger.loggerpos_set.create(
            screen = screen,
            start_date = tz.localize(parse(options['start'])),   
            refpnt = screen.refpnt,
            depth = depth,
            remarks = 'Moved from {}'.format(curpos.screen)
            )
        curpos.end_date = newpos.start_date
        curpos.save()
        logger.info('Moved logger {} from {} to {}'.format(datalogger,curpos.screen,newpos.screen))

        candidates = curpos.logger.datasource.filter(start__gte=curpos.start_date,stop__lte=curpos.end_date)
        curpos.files.remove(candidates)
        newpos.files.add(candidates)
        logger.info('{} files moved from {} to {}'.format(added,curpos,newpos)
        