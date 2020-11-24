import logging

from django.core.management.base import BaseCommand

from acacia.meetnet.models import LoggerPos
from datetime import timedelta
from acacia.data.models import Series, aware
from acacia.meetnet.util import recomp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'corrigeer voor offset nieuwe loggers'

    def add_arguments(self, parser):
        parser.add_argument('-d','--dry',action='store_true',dest='dry',help='Dry run: do not correct sensor depth')
        parser.add_argument('-w','--well',dest='well',help='Name of well')
    
    def handle(self, *args, **options):
        baro = Series.objects.get(name='Luchtdruk Voorschoten')
        
        # tolerantie voor aanpassingen
        limit = 0.1
        tolerance = timedelta(hours=4)

        dry = options.get('dry')
        well = options.get('well')

        queryset = LoggerPos.objects.all()
        if well:
            queryset = LoggerPos.objects.filter(screen__well__name=well)
            
        # nwe loggers: serienummer = 2005xxxx
        queryset = queryset.filter(logger__serial__startswith='2005')
        
        for pos in queryset.order_by('screen__well'):
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
            
            hpa = baro.at(logger_date).value
            if baro.unit.startswith('0.1'):
                hpa *= 0.1
            verschil = loggerwaarde-handpeiling
            offset = 0.01 * (hpa - 1013) / 0.98123 # offset door luchtdruk verschil
            if abs(verschil) < limit and (logger_date - hand_date < tolerance):
                # pas bkb aan en rond af op mm
                refpnt = round(pos.refpnt+offset,3)
                logger.debug('{},{},{},{:+.1f} cm'.format(pos, pos.refpnt, refpnt, offset*100))
                if not dry:
                    pos.remarks = 'ophangpunt {} aangepast met {:+.2f} cm voor luchtdruk van {:.1f} hPa tijdens installatie.'.format(pos.refpnt, offset*100, hpa)
                    pos.refpnt = refpnt
                    pos.save()
                    series = screen.find_series()
                    if series:
                        success = recomp(screen, series, start=pos.start_date,stop=pos.end_date)
                    