# Create your views here.
from django.shortcuts import render_to_response
from django.http import HttpResponse

def Index(request):
    return render_to_response('Main/Index.html', {})
