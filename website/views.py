from django.shortcuts import render


def error_400(request, exception):
        data = {}
        return render(request,'website/error_400.html', data)

def error_403(request, exception):
        data = {}
        return render(request,'website/error_403.html', data)

def error_404(request, exception):
        data = {}
        return render(request,'website/error_404.html', data)

def error_500(request):
        data = {}
        return render(request,'website/error_500.html', data)
