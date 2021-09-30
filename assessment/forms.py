from django import forms


class ReportIntervalForm(forms.Form):
    date_since = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    time_since = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'time'}), required=False)

    date_until = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    time_until = forms.DateTimeField(widget=forms.DateInput(attrs={'type': 'time'}), required=False)
