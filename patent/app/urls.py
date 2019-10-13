"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

app_name = "app"

from django.conf.urls import url
from app import views

urlpatterns = [
    url(r'^main/', views.main, name = "main"),
    url(r'^db/', views.db, name = "db"),
    url(r'^search/$', views.search, name="search"),
    url(r'^select_db/$', views.select_db, name="select_db"),
    url(r'^delete_db/$', views.delete_db, name="delete_db"),
    url(r'^insert_db/$', views.insert_db, name="insert_db"),
    url(r'^update_db/$', views.update_db, name="update_db"),
    url(r'^get_derived_query_list/', views.get_derived_query_list, name="get_derived_query_list"),
    url(r'^get_task_result/$', views.get_task_result, name="get_task_result"),
    url(r'^get_sample_result/$', views.get_sample_result, name="get_sample_result"),
    url(r'^stop_task/', views.stop_task, name="stop_task")
]