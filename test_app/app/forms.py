from django import forms

from test_app.app.models import ModelWithFileField


class TestUploadForm(forms.ModelForm):
    class Meta:
        model = ModelWithFileField
        fields = ['file']
