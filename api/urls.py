from django.urls import path, include
from .views import (
    AddNewModel,
    WarrantyLookup
)

urlpatterns = [
    path('model', AddNewModel.as_view()),
    path('warranty', WarrantyLookup.as_view()),
]