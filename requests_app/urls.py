from django.urls import path

from . import views

urlpatterns = [
    # Employee
    path("request/", views.request_create, name="request_create"),
    path("mine/", views.my_requests, name="my_requests"),
    path("return/<int:pk>/", views.return_my_asset, name="return_my_asset"),

    # Manager
    path("approvals/", views.approval_queue, name="approval_queue"),
    path("approve/<int:pk>/", views.request_approve, name="request_approve"),
    path("reject/<int:pk>/", views.request_reject, name="request_reject"),
]
