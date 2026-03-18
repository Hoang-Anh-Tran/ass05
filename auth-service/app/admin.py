from django.contrib import admin
from .models import AuthUser, RefreshToken

admin.site.register(AuthUser)
admin.site.register(RefreshToken)
