from django import forms

class UrlForm(forms.Form):
    verify_url = forms.CharField(label='Entrer une url', max_length=1000)