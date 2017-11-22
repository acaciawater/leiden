# -*- coding: utf-8 -*-
'''
Created on Oct 31, 2017

@author: theo
'''
import logging
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Screen
from acacia.meetnet.actions import make_wellcharts

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clean timeseries. Remove dry points and points before date of installation'
    
    def add_arguments(self, parser):
        parser.add_argument('-s','--screen',
                action='store',
                type=str,
                dest='screen')

    def handle(self, *args, **options):
        for screen in Screen.objects.all(): 
            if screen.loggerpos_set.exists():
                refpnt = screen.refpnt or 0
                series = screen.find_series()
                first = screen.loggerpos_set.earliest('start_date')
                deleted, _what = series.datapoints.filter(date__lt=first.start_date).delete()
                for pos in screen.loggerpos_set.all():
                    depth = pos.depth
                    min_level = refpnt - depth + 0.010 # 10 mm above sensor
                    pts = series.filter_points(start=pos.start_date,stop=pos.end_date).filter(value__lt=min_level)
                    count, _what = pts.delete()
                    deleted += count                
                if deleted:
                    logger.info('{} points deleted for {}'.format(deleted-1,screen)) 
                make_wellcharts(modeladmin=None, request=None, queryset=[screen.well])
                