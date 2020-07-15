import logging

from django.core.management.base import BaseCommand

from acacia.meetnet.models import Datalogger, Well
import pytz
import pandas as pd
from acacia.data.models import Generator
from django.conf import settings
from django.contrib.auth.models import User
import json

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Groot onderhoud juli 2020'
    
    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):
        filename = options['filename']
        df = pd.read_excel(filename)
        tz = pytz.timezone('Europe/Amsterdam')
        gen = Generator.objects.get(name='Ellitrack')
        admin = User.objects.filter(is_superuser=True).first()
        
        for index, row in df.iterrows():
            pb = row['peilbuis']
            try:
                oud = '%d' % row['oude logger ID']
                nieuw = '%d' % row['nieuwe Logger ID']
            except TypeError:
                continue
            bkb = row['bovenkant peilbuis-maaiveld(cm)'] / 100
            lengte = row['diepte peilbuis'] / 100
            draad = row['Draadlengte (cm)'] / 100
            datum = row['datum']
            tijd = row['tijd vervanging']
            
            well = Well.objects.get(name__iexact=pb)
            screen = well.screen_set.get(nr=1)

            datum = tz.localize(datum.replace(hour=tijd.hour,minute=tijd.minute))
            diepte = lengte + bkb 
            bkb = well.maaiveld - bkb
            
            install = screen.loggerpos_set.latest('start_date')
            logger.debug(install)

            if abs(screen.depth - diepte) > 1e-4:
                logger.error('peilbuis diepte aanpassen van %.2f naar %.2f' % (screen.depth, diepte))
                screen.depth = diepte
                screen.save(update_fields=('depth',))
            if abs(screen.refpnt - bkb) > 1e-4:
                logger.error('bovenkant peilbuis aanpassen van %.2f naar %.2f' % (screen.refpnt, bkb))
                screen.refpnt = bkb
                screen.save(update_fields=('refpnt',))

            if install.logger.serial == oud:
                # stop datasources
                install.logger.datasources.all().update(autoupdate=False)
    
                # end installation 
                install.end_date=datum
                install.save(update_fields=('end_date',))
            
            # create and install new logger
            datalogger, _created = Datalogger.objects.get_or_create(serial=nieuw, model='etd2')
            datasource, _created = datalogger.datasources.update_or_create(
                name = nieuw,
                meetlocatie = screen.mloc,
                defaults = {
                    'description': 'Ellitrack D2 logger (niet gecompenseerd voor luchtdruk)',
                    'generator': gen,
                    'user': admin,
                    'config': json.dumps({'logger': nieuw,'compensated': True}),
                    'timezone': 'Etc/GMT-1',
                    'url': settings.FTP_URL,
                    'username': settings.FTP_USERNAME,
                    'password': settings.FTP_PASSWORD,
                })
            
            pos, created = screen.loggerpos_set.update_or_create(logger=datalogger,start_date=datum,defaults={'refpnt':screen.refpnt,'depth':draad})
            if created:
                logger.debug('Created %s' % pos)
            