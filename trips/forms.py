from django import forms
from .models import Trip

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = [
            'title', 'description', 'start_date', 'end_date',
            'origin', 'destination', 'transport_type', 'transport_custom',
            'budget_per_person', 'max_participants',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

from .models import Proposal

class ProposalForm(forms.ModelForm):
    class Meta:
        model = Proposal
        fields = ['title', 'description', 'cost', 'link']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

from .models import Activity

class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'description', 'cost', 'link', 'start_time', 'end_time']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }
