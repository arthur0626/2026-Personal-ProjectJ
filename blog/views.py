from django.shortcuts import render


def index(request):
    return render(request, 'blog/index.html')


def detail(request, slug):
    return render(request, 'blog/detail.html', {'slug': slug})
