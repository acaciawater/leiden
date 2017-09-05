'''
Created on Sep 5, 2017

@author: theo
'''
from acacia.meetnet.models import Network
from acacia.data.models import Project
from django.contrib.gis.geos import Point
from acacia.data.util import RDNEW
from django.core.management.base import BaseCommand
import logging
import csv 
from datetime import datetime
logger = logging.getLogger(__name__)

def asfloat(x):
    try:
        return float(x)
    except:
        return None

class Command(BaseCommand):
    help = 'Import csv file with well data'
    
    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        files = options['files']
        net = Network.objects.first()
        prj = Project.objects.first()
        for fname in files:
            logger.info('Importing wells from {}'.format(fname))
            with open(fname) as f:
                numcreated = 0
                numupdated = 0
                reader = csv.DictReader(f)
                for row in reader:
                    x = float(row['x'])
                    y = float(row['y'])
                    name = row['naam']
                    nitg = row['nitg']
                    try:
                        loc = Point(x,y,srid=RDNEW)
                        ploc, created = prj.projectlocatie_set.get_or_create(name=name,defaults={'location':loc})
                        well, created = ploc.well_set.update_or_create(name=name,defaults={
                            'network': net,
                            'nitg': nitg,
                            'location': loc,
                            'maaiveld':float(row['maaiveld']),
                            'description':row['omschrijving'],
                            'straat': row['straat'],
                            'postcode': row['postcode'],
                            'plaats': row['plaats'],
                            'date':datetime(2017,9,1)
                            })
                        if created:
                            logger.info('Added well {well}'.format(well=name))
                            numcreated += 1 
                        else:
                            logger.info('Updated well {well}'.format(well=name))
                            numupdated += 1 
                    except Exception as e:
                        logger.error('{}: {}'.format(name,e))
                
        logger.info('Import completed, {} created, {} updated'.format(numcreated,numupdated))
