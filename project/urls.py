from project import views
from django.urls import path

urlpatterns = [
    path('<int:project_id>/mrs', views.GetMergeRequests.as_view()),
]