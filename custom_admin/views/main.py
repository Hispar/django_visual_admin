from collections import OrderedDict
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.admin import FieldListFilter
from django.contrib.admin.exceptions import (
    DisallowedModelAdminLookup, DisallowedModelAdminToField,
)
from django.contrib.admin.options import (
    IS_POPUP_VAR, TO_FIELD_VAR, IncorrectLookupParameters,
)
from django.contrib.admin.utils import (
    get_fields_from_path, prepare_lookup_value, quote,
)
from django.core.exceptions import (
    FieldDoesNotExist, ImproperlyConfigured, SuspiciousOperation,
)
from django.core.paginator import InvalidPage
from django.db import models
from django.db.models.expressions import Combinable, F, OrderBy
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timezone import make_aware
from django.utils.translation import gettext
from django.contrib.admin.views.main import ChangeList as BaseChangeList

# Changelist settings
from custom_admin.utils import lookup_needs_distinct

ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
SEARCH_VAR = 'q'
ERROR_FLAG = 'e'

IGNORED_PARAMS = (
    ALL_VAR, ORDER_VAR, ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, TO_FIELD_VAR)


class ChangeList(BaseChangeList):

    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        return reverse('custom_admin:%s_%s_change' % (self.opts.app_label,
                                                      self.opts.model_name),
                       args=(quote(pk),),
                       current_app=self.model_admin.admin_site.name)
