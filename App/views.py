from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request, 'home.html')


def login(request):
    return render(request, 'login.html')
    
def titulo_otorgado(request):
    return render(request, 'titulo_otorgado.html')

def certificacion_titulo(request):
    return render(request, 'certificacion_titulo.html')

def publicacion_gaceta(request):
    return render(request, 'publicacion_gaceta.html')

def acta_culminacion(request):
    return render(request, 'acta_culminacion.html')

def plan_estudios(request):
    return render(request, 'plan_estudios.html')