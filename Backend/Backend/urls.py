"""
URL configuration for Backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from smartConnect.views import smartConnectAlgorithm
from smartMentor.views import mentorMatchingAlgorithm
from tokenGenerator1.views import generateToken1
from queryExecute.views import fetchUserInfo, institution_list, upsert_user

urlpatterns = [
    path('fquery/changeUser', upsert_user, name = 'changeUser'),
    path('fquery/fetchInstitution', institution_list, name = 'fetchInstitution'),
    path('fquery/fetchUser', fetchUserInfo, name = 'fetchUser'),
    path('smartConnect/', smartConnectAlgorithm, name='smartConnect'),
    path('mentorMatching/', mentorMatchingAlgorithm, name='mentorMatching'),
    path('generateToken1/', generateToken1, name='generateToken1'),
    path('admin/', admin.site.urls),
]
