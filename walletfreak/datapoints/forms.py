from django import forms
from .models import DataPoint

class DataPointForm(forms.Form):
    card_slug = forms.CharField(max_length=100)
    card_name = forms.CharField(max_length=200)
    card_name = forms.CharField(max_length=200)
    benefit_name = forms.CharField(max_length=200)
    benefit_id = forms.CharField(max_length=200, required=False)
    status = forms.ChoiceField(choices=[('Success', 'Success'), ('Failed', 'Failed')])
    content = forms.CharField(widget=forms.Textarea)
    transaction_date = forms.DateField(required=False)
    cleared_date = forms.DateField(required=False)
