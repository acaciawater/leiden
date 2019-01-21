'''
Created on Jan 25, 2018

@author: theo
'''

from django.forms.models import ModelForm
from acacia.data.models import DataPoint
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, MultiField, HTML
from django import forms
from django.utils.translation import ugettext_lazy as _
from acacia.meetnet.models import Well, Network
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
import datetime
from django.forms.widgets import SelectDateWidget
from django.contrib.gis.geos.point import Point

class DatapointForm(ModelForm):
    mark_delete = forms.BooleanField()
    class Meta:
        model = DataPoint
        exclude = ('series',)

class DatapointFormsetHelper(FormHelper):
    def __init__(self,*args,**kwargs):
        super(DatapointFormsetHelper, self).__init__(*args, **kwargs)
        self.form_method = 'post'
        self.field_template = 'bootstrap3/layout/inline_field.html'
        self.layout = Layout(
            'date',
            'value',
        )
        self.render_required_fields = True

SRS_CHOICES = (
    (4326,'WGS84'),
    (28992,'Rijksdriehoekstelsel')
    )
LOGGER_CHOICES = (
    ('Diver','Diver'),
    ('Ellitrack','Ellitrack')
    )

class AddWellForm(forms.Form):
    network = forms.ModelChoiceField(queryset=Network.objects.all(),initial=Network.objects.first())
    name = forms.CharField(max_length=50)
    srid = forms.ChoiceField(choices=SRS_CHOICES,label=_('Coordinate system'),initial=28992)
    xcoord = forms.FloatField(label=_('X-Coordinate'))
    ycoord = forms.FloatField(label=_('Y-Coordinate'))
    zcoord = forms.FloatField(label=_('Z-Coordinate'),help_text=_('Surface level in m above sea level'))
    date = forms.DateField(label=_('Construction date'),initial=datetime.date.today)

    refpnt = forms.FloatField(label=_('Top of casing'),help_text=_('Usually top of casing.'))
    top = forms.FloatField(label=_('Top of screen'))
    bottom = forms.FloatField(label=_('Bottom of screen'))
    depth = forms.FloatField(label=_('Bottom of casing'))
    logger_type = forms.ChoiceField(choices=LOGGER_CHOICES,label=_('Type of logger'),initial='Ellitrack')
    serial = forms.CharField(max_length=50,label=_('Logger serial number'))
    logger_depth = forms.FloatField(label=_('Depth of logger'))
    
    def clean(self):
        super(AddWellForm,self).clean()
        network = self.cleaned_data['network']
        name = self.cleaned_data['name']
        try:
            network.well_set.get(name=name)
            raise forms.ValidationError('A well with name "{}" already exists.'.format(name))
        except Well.DoesNotExist:
            pass
        srid = self.cleaned_data['srid']
        x = self.cleaned_data['xcoord']
        y = self.cleaned_data['ycoord']
        z = self.cleaned_data['zcoord']
        p = Point(x,y,srid=int(srid))
        error = False
        if srid != 4326:
            try:
                x,y = p.transform(4326,True).tuple
            except:
                error = True
        if error or (x < 2 or x > 8 or y < 50 or y > 54):
            raise forms.ValidationError('Coordinates of the well are not in The Netherlands.')
        
        ref = self.cleaned_data['refpnt']
        top = self.cleaned_data['top']
        bottom = self.cleaned_data['bottom']
        depth = self.cleaned_data['depth']
        if z and abs(ref-z) > 2:
            self.add_error('refpnt', 'top of casing differs too much from surface level.')
            self.add_error('zcoord', 'surface level differs too much from top of casing.')
        if top < bottom:
            self.add_error('top','top of screen should be above bottom.')
        if bottom < depth:
            self.add_error('bottom','bottom of screen should be above bottom of casing.')
        
        logger_depth = self.cleaned_data['logger_depth']
        if logger_depth < depth:
            self.add_error('logger_depth','Logger can not be installed below bottom of casing.')

    def __init__(self, *args, **kwargs):
        super(AddWellForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<h2>General well info</h2>'),
            Row(
                Column('network', css_class='form-group col-md-3 mb-0'),
                Column('name', css_class='form-group col-md-3 mb-0'),
                Column('date', css_class='form-group col-md-2 mb-0'),
                css_class = 'form-row'
            ),
            HTML('<h2>Coordinates</h2>'),
            Row(
                Column('srid', css_class='form-group col-md-3 mb-0'),
                Column('xcoord', css_class='form-group col-md-2 mb-0'),
                Column('ycoord', css_class='form-group col-md-2 mb-0'),
                Column('zcoord', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
            HTML('<h2>Casing and screen info</h2>'),
            Row(
                Column('refpnt', css_class='form-group col-md-2 mb-0'),
                Column('depth', css_class='form-group col-md-2 mb-0'),
                Column('top', css_class='form-group col-md-2 mb-0'),
                Column('bottom', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
            HTML('<h2>Logger info</h2>'),
            Row(
                Column('logger_type', css_class='form-group col-md-4 mb-0'),
                Column('serial', css_class='form-group col-md-2 mb-0'),
                Column('logger_depth', css_class='form-group col-md-2 mb-0'),
                css_class='form-row'
            ),
                                    
            Submit('submit', 'Submit')
        )