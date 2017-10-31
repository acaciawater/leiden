# -*- coding: utf-8 -*-
'''
Created on Oct 27, 2017

@author: theo
'''
import binascii
import logging
import os
import re

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from acacia.data.models import Generator, SourceFile
from acacia.meetnet.models import Network, LoggerDatasource


logger = logging.getLogger(__name__)

def asfloat(x):
    try:
        return float(x)
    except:
        return None

class Command(BaseCommand):
    help = 'Import csv files exported from ellitrack site'
    
    def add_arguments(self, parser):
        parser.add_argument('-d','--dir',
                action='store',
                type=str,
                dest='dirname')
        parser.add_argument('-f','--file',
                action='store',
                type=str,
                dest='filename')

    def addfile(self,filename):
        pass

    def handle(self, *args, **options):
        dirname = options.get('dirname',None)
        filename = options.get('filename',None)
        if not dirname or filename:
            logger.error('supply either dirname or filename')
            return
        admin = User.objects.get(username='theo')
        if dirname:
            for root,_path,files in os.walk(dirname):
                for filename in files:
                    match = re.match('^export-(?P<serial>\d+)-\d{4}-',filename)
                    if match:
                        serial = match.group('serial')
                        try:
                            ds = LoggerDatasource.objects.get(name=serial)
                        except LoggerDatasource.DoesNotExist:
                            logger.warning('Logger {} is not defined'.format(serial))
                            continue
                        with open(os.path.join(root,filename),'r') as f:
                            contents = f.read()
                            crc = binascii.crc32(contents)
                            exist = ds.sourcefiles.filter(crc=crc).first()
                            if exist:
                                logger.warning('Sourcefile {} already exists for logger {}'.format(filename,serial))
                                continue
                            sf = SourceFile(name=filename,datasource=ds,user=admin,crc=crc)
                            sf.file.save(filename, ContentFile(contents), save=True)
                            logger.info('Added {}'.format(filename))
