from django.urls import path
from . import views
urlpatterns = [
    path('',views.homePage, name='user-home-page'),
    path("login/", views.loginPage, name='user-login-page'),
    path("register/", views.registerPage, name='user-register-page'),
    path("logout/", views.logoutPage, name ='user-logout'),
    path("transfer/", views.transferPage, name ='user-transfer-page'),
    path("transactions/", views.transactionPage, name ='user-transaction-page'),
    path("transactions/<int:transaction_id>/", views.transactionDetailPage, name ='user-transaction-detail-page'),
    path("deposit/", views.depositPage, name ='user-deposit-page'),
    path("pin/", views.pinPage, name ='user-pin-page'),
    path("update-detail/", views.updateDetailPage, name ='user-update-detail-page'),
    path("success/", views.successPage, name ='user-success-page'),
    path("search-account/", views.searchPage, name ='user-search-account-page'),
]
