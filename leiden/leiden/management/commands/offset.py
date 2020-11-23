import logging

from django.core.management.base import BaseCommand

from acacia.meetnet.models import LoggerPos
from datetime import timedelta

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Vind offset nieuwe loggers'
    
    def handle(self, *args, **options):
        # nwe loggers: serienummer = 2005xxxx
        for pos in LoggerPos.objects.filter(logger__serial__startswith='2005').order_by('screen__well'):
            screen = pos.screen
            start = pos.start_date
            start_date=(start-timedelta(days=1)).date()
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
            
            logger.debug('pos: {}, start: {}, hand: {},{}, logger: {},{}, verschil: {}'.format(
                pos, start, hand_date, handpeiling, logger_date, loggerwaarde, loggerwaarde-handpeiling)
                )
            