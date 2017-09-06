'''
Created on Feb 21, 2015

@author: theo
'''
from acacia.meetnet.views import NetworkView
from acacia.meetnet.models import Network, Well
from django.contrib.gis.gdal.srs import SpatialReference, CoordTransform 
from django.http.response import JsonResponse, HttpResponseServerError
from django.views.generic.detail import DetailView

class HomeView(NetworkView):
    template_name = 'leiden/leaflet_map.html'

    def get_context_data(self, **kwargs):
        context = NetworkView.get_context_data(self, **kwargs)
        return context

    def get_object(self):
        return Network.objects.first()

class PopupView(DetailView):
    """ returns html response for leaflet popup """
    model = Well
    template_name = 'leiden/popup.html'
    
def well_locations(request):
    """ return json response with well locations
    """
    result = []
    trans = None
    for p in Well.objects.all():
        try:
            pnt = p.location
            if trans is None:
                wgs84 = SpatialReference(4326)
                rdnew = SpatialReference(28992)
                trans = CoordTransform(rdnew,wgs84)
            pnt.transform(trans)
            result.append({'id': p.id, 'name': p.name, 'nitg': p.nitg, 'description': p.description, 'lon': pnt.x, 'lat': pnt.y})
        except Exception as e:
            return HttpResponseServerError(unicode(e))
    return JsonResponse(result,safe=False)
    