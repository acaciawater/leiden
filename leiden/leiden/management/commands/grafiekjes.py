'''
Created on Dec 6, 2014

@author: theo
'''
from django.core.management.base import BaseCommand
from acacia.meetnet.models import Well

import os
import matplotlib.pyplot as plt
import logging
import dateutil
from os import makedirs
from acacia.meetnet.util import chart_for_well
from acacia.data.util import slugify
from django.utils.timezone import now
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    args = ''
    help = 'plot grafiekje(s)'

    def add_arguments(self, parser):
        parser.add_argument('-d','--dest', default='.', help='destination folder')
        parser.add_argument('-r', '--regex', type=str, help='well filter (regex)')
        parser.add_argument('--start', default='2020-06-01', help='first date')
        parser.add_argument('--stop', help='last date')
                        
    def handle(self, *args, **options):
        dest = options.get('dest')
        pattern = options.get('regex')
        start = options.get('start')
        stop = options.get('stop')
        if start:
            start = dateutil.parser.parse(start)
        if stop:
            stop = dateutil.parser.parse(stop)
        else:
            stop = now()
        if not os.path.exists(dest):
            makedirs(dest)
        query = Well.objects.filter(name__iregex=pattern)
        for w in query:
            logger.debug(w)
            img = chart_for_well(w,start,stop)
            name = slugify(w.name)
            with open(os.path.join(dest,name+'.png'),'wb') as f:
                f.write(img)
        