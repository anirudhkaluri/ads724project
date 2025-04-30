from django.contrib import admin
from django.urls import path
from .views import save_data, ask_llm, sayHi
urlpatterns = [
   path('save',save_data,name='save'),
   path('ask',ask_llm,name="ask"),
   path('sayHi',sayHi,name="hi")
]
