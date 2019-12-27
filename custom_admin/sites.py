from functools import update_wrapper
from weakref import WeakSet

from django.apps import apps
from django.contrib.admin import ModelAdmin, actions
from django.contrib.admin.sites import AlreadyRegistered, NotRegistered
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db.models.base import ModelBase
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import NoReverseMatch, reverse
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string
from django.utils.text import capfirst
from django.utils.translation import gettext as _, gettext_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.i18n import JavaScriptCatalog

from django.contrib.admin.sites import AdminSite as BaseAdminSite

from custom_admin.utils import flatten
from django_visual_admin.admin import CONFIGURATION, APP_CONFIGURATION, MODEL_CONFIGURATION

all_sites = WeakSet()


class AdminSite(BaseAdminSite):
    index_template = 'custom_admin/index.html'
    app_index_template = 'custom_admin/app_index.html'

    def __init__(self, name='custom_admin'):
        super().__init__(name)
        self.custom_registry = dict()

    @staticmethod
    def _get_custom_apps_models():
        return MODEL_CONFIGURATION

    @staticmethod
    def _get_custom_models_list_by_app(app_label):
        return [app_model for app_model, app_key in MODEL_CONFIGURATION.items() if
                APP_CONFIGURATION[app_key]['slug'] == app_label]

    @staticmethod
    def _get_custom_apps():
        return APP_CONFIGURATION

    # def admin_view(self, view, cacheable=False):
    #     """
    #     Decorator to create an admin view attached to this ``AdminSite``. This
    #     wraps the view and provides permission checking by calling
    #     ``self.has_permission``.
    #
    #     You'll want to use this from within ``AdminSite.get_urls()``:
    #
    #         class MyAdminSite(AdminSite):
    #
    #             def get_urls(self):
    #                 from django.urls import path
    #
    #                 urls = super().get_urls()
    #                 urls += [
    #                     path('my_view/', self.admin_view(some_view))
    #                 ]
    #                 return urls
    #
    #     By default, admin_views are marked non-cacheable using the
    #     ``never_cache`` decorator. If the view can be safely cached, set
    #     cacheable=True.
    #     """
    #
    #     def inner(request, *args, **kwargs):
    #         if not self.has_permission(request):
    #             if request.path == reverse('admin:logout', current_app=self.name):
    #                 index_path = reverse('admin:index', current_app=self.name)
    #                 return HttpResponseRedirect(index_path)
    #             # Inner import to prevent django.contrib.admin (app) from
    #             # importing django.contrib.auth.models.User (unrelated model).
    #             from django.contrib.auth.views import redirect_to_login
    #             return redirect_to_login(
    #                 request.get_full_path(),
    #                 reverse('admin:login', current_app=self.name)
    #             )
    #         return view(request, *args, **kwargs)
    #
    #     if not cacheable:
    #         inner = never_cache(inner)
    #     # We add csrf_protect here so this function can be used as a utility
    #     # function for any view, without having to repeat 'csrf_protect'.
    #     if not getattr(view, 'csrf_exempt', False):
    #         inner = csrf_protect(inner)
    #     return update_wrapper(inner, view)

    def get_urls(self):
        from django.urls import include, path, re_path
        # Since this module gets imported in the application's root package,
        # it cannot import models from other applications at the module level,
        # and django.contrib.contenttypes.views imports ContentType.
        from django.contrib.contenttypes import views as contenttype_views

        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)

            wrapper.admin_site = self
            return update_wrapper(wrapper, view)

        # Admin-site-wide views.
        urlpatterns = [
            path('', wrap(self.index), name='index'),
            path('login/', self.login, name='login'),
            path('logout/', wrap(self.logout), name='logout'),
            path('password_change/', wrap(self.password_change, cacheable=True), name='password_change'),
            path(
                'password_change/done/',
                wrap(self.password_change_done, cacheable=True),
                name='password_change_done',
            ),
            path('jsi18n/', wrap(self.i18n_javascript, cacheable=True), name='jsi18n'),
            path(
                'r/<int:content_type_id>/<path:object_id>/',
                wrap(contenttype_views.shortcut),
                name='view_on_site',
            ),
        ]

        custom_models = self._get_custom_apps_models()
        custom_apps = self._get_custom_apps()

        # Add in each model's views, and create a list of valid URLS for the
        # app_index
        valid_app_labels = []
        for model, model_admin in self._registry.items():
            if model.__name__ in custom_models.keys():
                self.custom_registry[model.__name__] = model_admin
            else:
                urlpatterns += [
                    path('%s/%s/' % (model._meta.app_label, model._meta.model_name), include(model_admin.urls)),
                ]
                if model._meta.app_label not in valid_app_labels:
                    valid_app_labels.append(model._meta.app_label)

        for model, app in custom_models.items():
            if model not in self.custom_registry.keys() or app not in custom_apps.keys():
                continue

            app_slug = custom_apps[app]['slug'] if 'slug' in custom_apps[app] else app.lower()

            urlpatterns += [
                path('%s/%s/' % (app_slug, model.lower()), include(self.custom_registry[model].urls)),
            ]
            if app_slug not in valid_app_labels:
                valid_app_labels.append(app_slug)

        # If there were ModelAdmins registered, we should have a list of app
        # labels for which we need to allow access to the app_index view,
        if valid_app_labels:
            regex = r'^(?P<app_label>' + '|'.join(valid_app_labels) + ')/$'
            urlpatterns += [
                re_path(regex, wrap(self.app_index), name='app_list'),
            ]

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), 'custom_admin', self.name

    def _build_app_dict(self, request, label=None):
        """
        Build the app dictionary. The optional `label` parameter filters models
        of a specific app.
        """
        app_dict = {}

        custom_models = self._get_custom_apps_models()
        custom_apps = self._get_custom_apps()

        if label:
            models = {
                m: m_a for m, m_a in self._registry.items()
                if m._meta.app_label == label
            }
            if not models:
                models = {
                    model: self.custom_registry[model_name] for model_name in self._get_custom_models_list_by_app(label)
                    for model in self._registry.keys() if model.__name__ == model_name
                }
        else:
            models = self._registry

        for model, model_admin in models.items():
            custom_model = model.__name__ in custom_models.keys()
            if custom_model:
                app_label = custom_apps[custom_models[model.__name__]]['slug']
            else:
                app_label = model._meta.app_label

            has_module_perms = model_admin.has_module_permission(request)
            if not has_module_perms:
                continue

            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True not in perms.values():
                continue

            info = (app_label, model._meta.model_name)
            model_dict = {
                'name': capfirst(model._meta.verbose_name_plural),
                'object_name': model._meta.object_name,
                'perms': perms,
                'admin_url': None,
                'add_url': None,
            }
            if perms.get('change') or perms.get('view'):
                model_dict['view_only'] = not perms.get('change')
                try:
                    model_dict['admin_url'] = reverse('custom_admin:%s_%s_changelist' % info, current_app=self.name)
                except NoReverseMatch:
                    # print(info)
                    pass
            if perms.get('add'):
                try:
                    model_dict['add_url'] = reverse('custom_admin:%s_%s_add' % info, current_app=self.name)
                except NoReverseMatch:
                    pass

            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
            else:
                if custom_model:
                    app_name = app_label
                    app_url = ''
                else:
                    app_name = apps.get_app_config(app_label).verbose_name

                try:
                    app_url = reverse(
                        'custom_admin:app_list',
                        kwargs={'app_label': app_label},
                        current_app=self.name,
                    )
                except NoReverseMatch:
                    pass

                app_dict[app_label] = {
                    'name': app_name,
                    'app_label': app_label,
                    'app_url': app_url,
                    'has_module_perms': has_module_perms,
                    'models': [model_dict],
                }

        if label:
            return app_dict.get(label)
        return app_dict

    def app_index(self, request, app_label, extra_context=None):
        app_dict = self._build_app_dict(request, app_label)
        if not app_dict:
            raise Http404('The requested admin page does not exist.')
        # Sort the models alphabetically within each app.
        app_dict['models'].sort(key=lambda x: x['name'])
        if app_label in self._get_custom_apps().keys():
            app_name = app_label
        else:
            app_name = apps.get_app_config(app_label).verbose_name

        context = {
            **self.each_context(request),
            'title': _('%(app)s administration') % {'app': app_name},
            'app_list': [app_dict],
            'app_label': app_label,
            **(extra_context or {}),
        }

        request.current_app = self.name

        return TemplateResponse(request, self.app_index_template or [
            'admin/%s/app_index.html' % app_label,
            'admin/app_index.html'
        ], context)


class DefaultAdminSite(LazyObject):
    def _setup(self):
        AdminSiteClass = import_string(apps.get_app_config('custom_admin').default_site)
        self._wrapped = AdminSiteClass()


# This global object represents the default admin site, for the common case.
# You can provide your own AdminSite using the (Simple)AdminConfig.default_site
# attribute. You can also instantiate AdminSite in your own code to create a
# custom admin site.
site = DefaultAdminSite()
