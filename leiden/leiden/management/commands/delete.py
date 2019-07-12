# -*- coding: utf-8 -*-
'''
Created on Jul 12, 2019

@author: theo
'''
import csv 
import logging

from django.core.management.base import BaseCommand
from django.utils import dateparse
import pytz

from acacia.meetnet.models import Network, Well

logger = logging.getLogger(__name__)

def asfloat(x):
    try:
        return float(x)
    except:
        return None

class Command(BaseCommand):
    help = 'Delete points'
    
    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)
        parser.add_argument('-d','--dry',action='store_true',default=False,dest='dry',help='Dry run: do not delete the datapoints')
        
    def handle(self, *args, **options):
        files = options['files']
        dry = options['dry']
        net = Network.objects.first()
#         tz = pytz.timezone('Europe/Amsterdam')
        tz = pytz.timezone('UTC')
        count = 0
        for fname in files:
            logger.info('Deleting measurements from {}'.format(fname))
            with open(fname) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        name = row['name']
                        start = tz.localize(dateparse.parse_datetime(row['from']))
                        stop = tz.localize(dateparse.parse_datetime(row['to']))
                    except Exception as e:
                        logger.error('{} skipped:{}'.format(unicode(row), e))
                        continue
                    if name and start and stop:
                        try:
                            well = Well.objects.get(network=net,name=name)
                            screen = well.screen_set.get(nr=1)
                            series = screen.find_series()
                            if series:
                                query = series.datapoints.filter(date__range=[start,stop])
                                if query:
                                    if dry:
                                        num_deleted = query.count()
                                    else:
                                        num_deleted, what = query.delete()
                                    count += num_deleted
                                    logger.info('{}: deleted {} points between {} and {}'.format(unicode(screen), num_deleted, start, stop))
                                else:
                                    logger.warning('{}: no points found between {} and {}'.format(unicode(screen), start, stop))
                        except Exception as e:
                            logger.error('{}: {}'.format(name,e))
                
        logger.info('Completed, {} datapoints deleted'.format(count))
