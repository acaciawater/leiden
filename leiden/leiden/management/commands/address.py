'''
Created on Sep 5, 2017

@author: theo
'''
from django.core.management.base import BaseCommand
import logging
 
from acacia.meetnet.models import Well
from leiden.postcode import get_address_rd, PostcodeException,\
    get_address_google
from acacia.data.util import toWGS84

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Adres gegevens ophalen bij postcode api'
    
    def add_arguments(self, parser):
        parser.add_argument('-w','--well',
                action='store',
                type=int,
                dest='pk')

    def handle(self, *args, **options):
        pk = options.get('pk',None)
        if pk:
            query = Well.objects.filter(pk=pk)
        else:
            query = Well.objects.all()
        for well in query:
            logger.info('Checking well {}'.format(well))
            try:
                loc = toWGS84(well.location)
                data = get_address_google(loc.x, loc.y)
                for address in data['results']:
                    logger.info(address.get('formatted_address','Geen adres'))
                    # first result is closest address
                    found = False
                    for comp in address['address_components']:
                        types = comp['types']
                        value = comp['long_name']
                        if 'street_number' in types:
                            well.huisnummer = value
                            found = True
                        elif 'route' in types:
                            well.straat = value
                            found = True
                        elif 'locality' in types:
                            well.plaats = value
                            found = True
                        elif 'postal_code' in types:
                            well.postcode = value
                            found = True
                    if found:
                        well.save()
                        break
            except PostcodeException as e:
                logger.error(e)
            

