from django.contrib import admin
from django.urls import path,include
from note import views

urlpatterns = [
    path('<imageName>/<int:pageNumber>',views.display_note,name='note-page-display'),
    path('shape',views.draw_shape, name='simple-shape'),
]
