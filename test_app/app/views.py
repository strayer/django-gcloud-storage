from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.edit import FormView

from test_app.app.forms import TestUploadForm
from test_app.app.models import ModelWithFileField

import django
if django.VERSION < (2, 0):
    from django.core.urlresolvers import reverse_lazy
else:
    from django.urls import reverse_lazy


class TestUploadView(FormView):
    template_name = 'test_upload_form.html'
    form_class = TestUploadForm
    success_url = reverse_lazy('upload_success')

    def form_valid(self, form):
        form.save()
        return super(TestUploadView, self).form_valid(form)


def file(request, id):
    testmodel = get_object_or_404(ModelWithFileField, pk=id)

    return HttpResponse(testmodel.file, content_type='text/plain')
