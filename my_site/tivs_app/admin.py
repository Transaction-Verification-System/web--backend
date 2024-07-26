from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(AppUser)
admin.site.register(BlackListModel)
admin.site.register(FailedCustomerData)
admin.site.register(PassedCustomerData)
admin.site.register(RePassedCustomerData)
admin.site.register(ErrorLogsModel)
admin.site.register(ECommercePassedModel)
admin.site.register(ECommerceFailedModel)
admin.site.register(ECommerceRePassedModel)
admin.site.register(ECommerceErrorModel)
admin.site.register(CreditCardPassedModel)
admin.site.register(CreditCardFailedModel)
admin.site.register(CreditRePassedModel)
admin.site.register(CreditCardErrorLogModel)