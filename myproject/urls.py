"""
URL configuration for myproject project.

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

from myproject.views.audio import AudioUploadView
from myproject.views.chat import ChatView
from myproject.views.pdf import PDFUploadView
from myproject.views.login import LoginView
from myproject.views.record import RecordView
from myproject.views.resume import ResumeView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/resume/", ResumeView.as_view(), name="resume"),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/upload_audio/', AudioUploadView.as_view(), name='upload_audio'),
    path('api/upload_pdf/', PDFUploadView.as_view(), name='upload_pdf'),
    path('api/send_chat_message/', ChatView.as_view(), name='send_chat_message'),
    path('api/record/<str:rid>/', RecordView.as_view()), 
    path('api/record/<str:rid>/<int:seq>/', RecordView.as_view()), 
]


