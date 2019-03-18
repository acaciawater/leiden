'''
Created on Feb 21, 2015

@author: theo
'''
from acacia.meetnet.views import NetworkView
from acacia.meetnet.models import Network, Well, Screen, Datalogger
from django.http.response import JsonResponse, HttpResponseServerError
from django.views.generic.detail import DetailView
import json
from django.conf import settings
from django.utils import timezone
from django.views.generic.edit import FormView
from leiden.forms import AddWellForm
from acacia.meetnet.util import set_well_address, register_well, register_screen
from django.contrib.gis.geos import Point
from acacia.data.models import Generator
from acacia.data.actions import generate_datasource_series
from acacia.meetnet.actions import make_wellcharts
import datetime
import pytz

def statuscolor(last):
    """ returns color for bullets on home page.
    Green is less than 1 day old, yellow is 1 - 2 days, red is 3 - 7 days and gray is more than one week old 
     """
    if last:
        now = timezone.now()
        age = now - last.date
        if age.days < 1:
            return 'green' 
        elif age.days < 2:
            return 'yellow'
        elif age.days < 7:
            return 'red' 
    return 'grey'

class HomeView(NetworkView):
    template_name = 'leiden/home.html'

    def get_context_data(self, **kwargs):
        context = NetworkView.get_context_data(self, **kwargs)
        options = {
            'center': [52.15478, 4.48565],
            'zoom': 12 }
        context['api_key'] = settings.GOOGLE_MAPS_API_KEY
        context['options'] = json.dumps(options)
        welldata = []
        for w in Well.objects.order_by('name'):
            last = w.last_measurement()
            welldata.append((w,last,statuscolor(last)))
        context['wells'] = welldata
        return context

    def get_object(self):
        return Network.objects.first()

class PopupView(DetailView):
    """ returns html response for leaflet popup """
    model = Well
    template_name = 'meetnet/well_info.html'
    
def well_locations(request):
    """ return json response with well locations
    """
    result = []
    for p in Well.objects.all():
        try:
            pnt = p.latlon()
            result.append({'id': p.id, 'name': p.name, 'nitg': p.nitg, 'description': p.description, 'lon': pnt.x, 'lat': pnt.y})
        except Exception as e:
            return HttpResponseServerError(unicode(e))
    return JsonResponse(result,safe=False)

class AddWellView(FormView):
    form_class = AddWellForm
    template_name = 'leiden/addwell.html'
    success_url = '/'

    def create_well(self, form):

        # create well
        network=form.cleaned_data['network']
        name=form.cleaned_data['name']
        srid=form.cleaned_data['srid']
        x = form.cleaned_data['xcoord']   
        y = form.cleaned_data['ycoord']   
        z = form.cleaned_data['zcoord']
        date = form.cleaned_data['date']   
        well = Well(network=network,name=name,location=Point(x,y,srid=int(srid)), maaiveld=z, date=date)
        set_well_address(well)
        register_well(well)

        # create screen
        ref = form.cleaned_data['refpnt']
        top = form.cleaned_data['top']
        bottom = form.cleaned_data['bottom']
        depth = form.cleaned_data['depth']
        screen = Screen(well=well,nr=1,refpnt=ref,top=top,bottom=bottom,depth=depth)
        register_screen(screen)

        # create logger
        serial = form.cleaned_data['serial']
        type = form.cleaned_data['logger_type']
        logger,created = Datalogger.objects.get_or_create(serial=serial,defaults={'model': '14' if type=='Diver' else 'etd2'})
        
        #create datasource
        options = {'user': self.request.user}
        if type == 'Diver':
            options.update({'generator': Generator.objects.get(name__iexact='Schlumberger'),
                            'autoupdate': False,
                            'timezone': 'CET', 
                            })
        else:
            options.update({'generator': Generator.objects.get(name__iexact='Ellitrack'),
                            'url': settings.FTP_URL,
                            'username': settings.FTP_USERNAME,
                            'password': settings.FTP_PASSWORD,
                            'timezone': 'Europe/Amsterdam',
                            })
        datasource, created = logger.datasources.get_or_create(name=serial, meetlocatie=screen.mloc, defaults=options)

        # create logger installation
        logger_depth = form.cleaned_data['logger_depth']
        logger.loggerpos_set.create(screen=screen,refpnt=ref,start_date=date,depth=logger_depth)

        def update():
            tz = pytz.timezone('CET')
            start = tz.localize(datetime.datetime(date.year,date.month,date.day))
            datasource.download(start)
            generate_datasource_series(None,self.request,[datasource])
            make_wellcharts(None,self.request,[well])
            
        # retrieve data in background
        from threading import Thread
        t = Thread(target=update)
        t.start()
                
    def form_valid(self, form):
        self.create_well(form)
        return super(AddWellView, self).form_valid(form)

    def get_context_data(self,*args,**kwargs):
        context = super(AddWellView, self).get_context_data(*args,**kwargs)
        context['object'] = Network.objects.first() # needed for logo and network name in template
        return context