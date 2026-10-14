from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.index, name='index'),
    path('drafts/', views.drafts, name='drafts'),
    path('drafts/new/', views.edit, name='new'),
    path('drafts/<int:pk>/', views.edit, name='edit'),
    path('drafts/<int:pk>/publish/', views.set_published, {'published': True}, name='publish'),
    path('drafts/<int:pk>/unpublish/', views.set_published, {'published': False}, name='unpublish'),
    path('uploads/', views.upload, name='upload'),
    path('comments/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('<slug:slug>/', views.detail, name='detail'),
    path('<slug:slug>/comments/', views.comment_create, name='comment_create'),
]
