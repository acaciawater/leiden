'''
Created on Feb 21, 2015

@author: theo
'''
from acacia.meetnet.views import NetworkView
from acacia.meetnet.models import Network, Well
from django.http.response import JsonResponse, HttpResponseServerError,HttpResponse
from django.views.generic.detail import DetailView
import json
from django.conf import settings
from django.utils import timezone

#from django.contrib.auth.decorators import login_required
#from django.forms.models import modelformset_factory
#from acacia.data.models import DataPoint, ManualSeries, Series
#from django.shortcuts import render, get_object_or_404
# from leiden.forms import DatapointForm, DatapointFormsetHelper
# 
# import django_tables2 as tables
# from crispy_forms.layout import Submit
# from django.urls.base import reverse
# from django.views.decorators.gzip import gzip_page
# 
# class DataPointTable(tables.Table):
#     class Meta:
#         model = DataPoint
#         template = 'django_tables2/bootstrap.html'
#         exclude = ('series', 'id')
# 
# @login_required
# def datapoint_editor2(request,pk):
#     network = Network.objects.first()
#     series = get_object_or_404(ManualSeries,pk=pk)
#     queryset = series.datapoints.all()
#     table = DataPointTable(queryset)
#     tables.RequestConfig(request).configure(table)
#     return render(request,'meetnet/datapoints.html',{'table': table, 'series': series, 'network': network}) 
#         
# @login_required
# def datapoint_editor1(request,pk):
#     DatapointFormset = modelformset_factory(DataPoint,form=DatapointForm, exclude=('series',))
#     network = Network.objects.first()
#     series = get_object_or_404(ManualSeries,pk=pk)
#     if request.method =='POST':
#         formset = DatapointFormset(request.POST)
#         if formset.is_valid():
#             pass
#     else:
#         series = get_object_or_404(ManualSeries,pk=pk)
#         formset = DatapointFormset(queryset=series.datapoints.order_by('date'))
#     return render(request,'meetnet/edit_datapoints.html',{'formset':formset, 'series': series, 'object': network}) 
# 
# @login_required
# def datapoint_editor3(request,pk):
#     DatapointFormset = modelformset_factory(DataPoint,form=DatapointForm, exclude=('series',))
#     helper = DatapointFormsetHelper()
#     helper.add_input(Submit("submit", "Save"))
#     helper.template = 'bootstrap/table_inline_formset.html'
#     network = Network.objects.first()
#     series = get_object_or_404(ManualSeries,pk=pk)
#     if request.method =='POST':
#         formset = DatapointFormset(request.POST)
#         if formset.is_valid():
#             pass
#     else:
#         series = get_object_or_404(ManualSeries,pk=pk)
#         formset = DatapointFormset(queryset=series.datapoints.order_by('date'))
#     return render(request,'meetnet/crispy_datapoints.html',{'formset':formset, 'helper': helper, 'series': series, 'object': network}) 
# 
# @login_required
# def datapoint_editor(request,pk):
#     network = Network.objects.first()
#     series = get_object_or_404(Series,pk=pk)
#     url = reverse('jexcel',args=[series.id])
#     return render(request,'meetnet/excel_datapoints.html',{'url':url, 'series': series, 'object': network}) 
# 
# @gzip_page
# def series_for_jExcel(request, pk):
#     s = get_object_or_404(Series,pk=pk)
#     pts = s.to_array()        
#     j = json.dumps(pts, default=lambda x: x.strftime('%Y-%m-%d %H:%M'))
#     return HttpResponse(j, content_type='application/json')

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
        for w in Well.objects.all():
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
    