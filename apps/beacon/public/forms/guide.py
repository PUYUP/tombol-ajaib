from django.forms import ModelForm

# PROJECT UTILS
from utils.generals import get_model

Guide = get_model('beacon', 'Guide')


class GuideForm(ModelForm):
    class Meta:
        model = Guide
        fields = ('label', 'category',)
