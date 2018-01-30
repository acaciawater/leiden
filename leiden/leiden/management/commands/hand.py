# -*- coding: utf-8 -*-
'''
Created on Jan 05, 2018

@author: theo
'''
import csv 
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import dateparse
import pytz

from acacia.data.models import ManualSeries
from acacia.meetnet.models import Network, Well

logger = logging.getLogger(__name__)

def asfloat(x):
    try:
        return float(x)
    except:
        return None

class Command(BaseCommand):
    help = 'Import manual measurements from csv'
    
    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        files = options['files']
        net = Network.objects.first()
        admin = User.objects.get(username='theo')
        tz = pytz.timezone('Europe/Amsterdam')
        for fname in files:
            logger.info('Importing manual measurements from {}'.format(fname))
            with open(fname) as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        name = row['ID']
                        date = tz.localize(dateparse.parse_datetime(row['Datum peiling']))
                        value = float(row['Waarde peiling'])
                    except Exception as e:
                        logger.warning('{} skipped:{}'.format(unicode(row), e))
                        continue
                    if name and date and value:
                        try:
                            well = Well.objects.get(network=net,name=name)
                            screen = well.screen_set.get(nr=1)
                            if not screen.refpnt:
                                logger.warning('Screen {} skipped: no top elevation defined'.format(unicode(screen)))
                                continue
                            name = '{} - HAND'.format(unicode(screen)) 
                            series, created = ManualSeries.objects.get_or_create(name = name, mlocatie = screen.mloc, defaults = {
                                'user': admin,
                                'type': 'scatter',
                                'timezone': tz.zone})
                            if created:
                                logger.info('Created manual series "{}"'.format(unicode(series)))
                            series.datapoints.update_or_create(date = date, defaults = {'value': screen.refpnt - value})
                        except Exception as e:
                            logger.error('{}: {}'.format(name,e))
                
        logger.info('Import completed')
