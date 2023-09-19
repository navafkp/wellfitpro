from django import forms

class SalesDateFilterForm(forms.Form):
    start_date = forms.CharField(label='Start Date and Time', widget=forms.TextInput(attrs={'type': 'text'}))
    end_date = forms.CharField(label='End Date and Time', widget=forms.TextInput(attrs={'type': 'text'}))