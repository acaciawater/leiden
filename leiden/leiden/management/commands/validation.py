# -*- coding: utf-8 -*-
'''
Created on Nov 26, 2019

@author: theo
'''
import os
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from acacia.meetnet.models import Well, Screen
from acacia.validation.views import process_file
from acacia.validation.models import Validation

logger = logging.getLogger(__name__)

def import_file(fname, user):
    name, _ext = os.path.basename(fname).split('.')
    try:
        well = Well.objects.get(name=name)
        screen = well.screen_set.get(nr=1)
        series = screen.find_series();
        if series is None:
            logger.error('No timeseries found for screen {}'.format(screen))
            return
        validation, created = Validation.objects.get_or_create(series=series)
        if created:
            logger.info('Validation created for {} of screen {}'.format(series, screen))
        logger.info('Processing {}'.format(fname))
        process_file(fname, user, pk=validation.pk)
        #validation.accept(user=user)
    except Well.DoesNotExist:
        logger.error('Well {} not found'.format(name))
    except Screen.DoesNotExist:
        logger.error('Screen 1 not found for well {}'.format(well))

class Command(BaseCommand):
    help = "Import Arjen's validation files"
    
    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str)

    def handle(self, *args, **options):
        admin = User.objects.get(username='theo')
        for arg in options['files']:
            if os.path.isdir(arg):
                for path, _dirs, files in os.walk(arg):
                    for fname in files:
                        if fname.endswith('.xlsx'):
                            import_file(os.path.join(path,fname), admin)
            else:
                import_file(arg, admin)
                