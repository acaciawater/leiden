import logging

from django.core.management.base import BaseCommand

from acacia.meetnet.models import LoggerPos
from datetime import timedelta
from acacia.data.models import Series, aware

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'corrigeer voor offset nieuwe loggers'

    def add_arguments(self, parser):
        parser.add_argument('-d','--dry',action='store_true',dest='dry',help='Dry run: do not correct sensor depth')
    
    def handle(self, *args, **options):
        baro = Series.objects.get(name='Luchtdruk Voorschoten')
        
        # tolerantie voor aanpassingen
        limit = 0.1
        tolerance = timedelta(hours=4)

        dry = options.get('dry')
        
        # nwe loggers: serienummer = 2005xxxx
        for pos in LoggerPos.objects.filter(logger__serial__startswith='2005').order_by('screen__well'):
            screen = pos.screen
            start_date = aware(pos.start_date-timedelta(days=1),'utc').replace(hour=0,minute=0,second=0)
            hand = screen.get_manual_series(start=start_date)
            if hand is None or hand.empty:
                continue
            hand_date = min(hand.index)
            handpeiling = hand[hand_date]
            
            levels = screen.get_compensated_series(start=hand_date).dropna()
            if levels is None or levels.empty:
                continue
            logger_date = min(levels.index)
            loggerwaarde = levels[logger_date]
            
            hpa = baro.at(logger_date)
            verschil = loggerwaarde-handpeiling
            if abs(verschil) < limit and (logger_date - hand_date < tolerance):
                # tel op bij kabellengte en rond af op mm
                depth = round(pos.depth+verschil,3)
                logger.debug('{},{},{},{:+.1f} cm'.format(pos, pos.depth, depth, verschil*100))
                if not dry:
                    pos.depth = depth
                    pos.save(update_fields=('depth',))
#                 logger.debug('{},{},{},{},{},{},{}'.format(
#                     pos, hand_date, handpeiling, logger_date, loggerwaarde, verschil, hpa.value)
#                     )
            