from django.urls import path, include
from .views import (
    index,
    AddNewModel,
    WarrantyLookup
)

urlpatterns = [
    path('', index, name='index'),
    path('model', AddNewModel.as_view()),
    path('warranty', WarrantyLookup.as_view()),
]
