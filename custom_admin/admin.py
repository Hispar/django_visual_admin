from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from custom_admin import AdminSite


class MyAdminSite(AdminSite):
    site_header = 'Custom Administration'


admin_site = MyAdminSite(name='custom_admin')
admin_site.register(get_user_model())
admin_site.register(Group)
