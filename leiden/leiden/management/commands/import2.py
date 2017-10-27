# -*- coding: utf-8 -*-
'''
Created on Oct 24, 2017

@author: theo
'''
from acacia.meetnet.models import Network, Well, Datalogger,\
    LoggerDatasource
from acacia.data.models import Project
from django.contrib.gis.geos import Point
from acacia.data.util import RDNEW
from django.core.management.base import BaseCommand
import logging
import csv 
from acacia.meetnet.util import register_well, register_screen
from datetime import datetime
from django.conf import settings
from acacia.data.models import Generator
from django.contrib.auth.models import User
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
        ellitrack = Generator.objects.get(name='Ellitrack')
        admin = User.objects.get(username='theo')
        for fname in files:
            logger.info('Importing wells from {}'.format(fname))
            with open(fname) as f:
                numcreated = 0
                numupdated = 0
                reader = csv.DictReader(f)
                for row in reader:
                    x = asfloat(row['X'])
                    y = asfloat(row['Y'])
                    name = row['peilbuisnr']
                    try:
                        loc = Point(x,y,srid=RDNEW)
                        description = unicode(row['Beschrijving'],'iso8859')
                        well, created = Well.objects.update_or_create(name=name,defaults={
                            'network': net,
                            'location': loc,
                            'description':description,
                            'date':datetime(2017,9,1)
                            })
                        if created:
                            register_well(well)
                        bottom = asfloat(row['peilbuisdiepte hand'] or row['peilbuisdiepte'])
                        top = bottom - 1 if bottom else None
                        refpnt = well.maaiveld or well.ahn # moet bovenkant buis worden!!
                        screen, created = well.screen_set.update_or_create(nr=1,defaults={'top': top, 'bottom': bottom, 'refpnt': refpnt})
                        if created:
                            register_screen(screen)
                            logger.info('Added {screen}'.format(screen=str(screen)))
                            numcreated += 1 
                        else:
                            logger.info('Updated {screen}'.format(screen=str(screen)))
                            numupdated += 1
                        serial = row['serienummer']
                        if serial:
                            datalogger, created = Datalogger.objects.get_or_create(serial=serial,defaults={'model':'etd'})
                            if created:
                                logger.info('Created logger {}'.format(serial))
                            install = row['Geinstalleerd op'] or '9/10/2017'
                            date = datetime.strptime(install,'%d/%M/%Y')
                            depth = asfloat(row['kabellengte'])
                            pos, created = datalogger.loggerpos_set.update_or_create(logger=datalogger,defaults={'screen': screen, 'start_date': date,'depth':depth})
                            if created:
                                logger.info('Installed {}'.format(pos))
                            else:
                                logger.info('Updated {}'.format(pos))

                            ds, created = LoggerDatasource.objects.update_or_create(
                                logger = datalogger,
                                name = serial,
                                defaults={'description': 'Ellitrack datalogger serienummer {}'.format(serial),
                                          'meetlocatie': screen.mloc,
                                          'timezone': 'Europe/Amsterdam',
                                          'user': admin,
                                          'generator': ellitrack,
                                          'url': settings.FTP_URL,
                                          'username': settings.FTP_USERNAME,
                                          'password': settings.FTP_PASSWORD,
                                          })
                            if created:
                                ds.locations.add(screen.mloc)
                                logger.info('Created datasource {}'.format(ds))

                            result = ds.download()
                            if result:
                                # download succeeded, create timeseries
                                ds.update_parameters()
                                for p in ds.parameter_set.all():
                                    series, created = p.series_set.get_or_create(
                                        mlocatie = screen.mloc, 
                                        name = p.name, 
                                        defaults = {'description': p.description, 
                                                    'unit': p.unit, 
                                                    'user': admin})
                                    if created:
                                        logger.info('Created timeseries {}'.format(series))
                                    series.update()
                    except Exception as e:
                        logger.error('{}: {}'.format(name,e))
                
        logger.info('Import completed, {} created, {} updated'.format(numcreated,numupdated))
