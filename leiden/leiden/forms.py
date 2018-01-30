'''
Created on Jan 25, 2018

@author: theo
'''

from django.forms.models import ModelForm
from acacia.data.models import DataPoint
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms

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
