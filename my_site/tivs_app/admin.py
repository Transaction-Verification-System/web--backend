from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(AppUser)
admin.site.register(BlackListModel)
admin.site.register(CustomerData)
admin.site.register(ErrorLogsModel)