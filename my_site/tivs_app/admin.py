from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(AppUser)
admin.site.register(BlackListModel)
admin.site.register(FailedCustomerData)
admin.site.register(PassedCustomerData)
admin.site.register(RePassedCustomerData)
admin.site.register(ErrorLogsModel)