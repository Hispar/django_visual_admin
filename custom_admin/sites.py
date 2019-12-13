from functools import update_wrapper
from weakref import WeakSet

from django.apps import apps
from django.contrib.admin import ModelAdmin, actions
from django.contrib.admin.sites import AlreadyRegistered, NotRegistered
from django.contrib.auth import REDIRECT_FIELD_NAME
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

all_sites = WeakSet()


class AdminSite(BaseAdminSite):

    def __init__(self, name='custom_admin'):
        super().__init__(name)

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

        # Add in each model's views, and create a list of valid URLS for the
        # app_index
        valid_app_labels = []
        for model, model_admin in self._registry.items():
            urlpatterns += [
                path('%s/%s/' % (model._meta.app_label, model._meta.model_name), include(model_admin.urls)),
            ]
            if model._meta.app_label not in valid_app_labels:
                valid_app_labels.append(model._meta.app_label)

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

    # def password_change(self, request, extra_context=None):
    #     """
    #     Handle the "change password" task -- both form display and validation.
    #     """
    #     from django.contrib.admin.forms import AdminPasswordChangeForm
    #     from django.contrib.auth.views import PasswordChangeView
    #     url = reverse('admin:password_change_done', current_app=self.name)
    #     defaults = {
    #         'form_class': AdminPasswordChangeForm,
    #         'success_url': url,
    #         'extra_context': {**self.each_context(request), **(extra_context or {})},
    #     }
    #     if self.password_change_template is not None:
    #         defaults['template_name'] = self.password_change_template
    #     request.current_app = self.name
    #     return PasswordChangeView.as_view(**defaults)(request)
    #
    # def password_change_done(self, request, extra_context=None):
    #     """
    #     Display the "success" page after a password change.
    #     """
    #     from django.contrib.auth.views import PasswordChangeDoneView
    #     defaults = {
    #         'extra_context': {**self.each_context(request), **(extra_context or {})},
    #     }
    #     if self.password_change_done_template is not None:
    #         defaults['template_name'] = self.password_change_done_template
    #     request.current_app = self.name
    #     return PasswordChangeDoneView.as_view(**defaults)(request)
    #
    # def i18n_javascript(self, request, extra_context=None):
    #     """
    #     Display the i18n JavaScript that the Django admin requires.
    #
    #     `extra_context` is unused but present for consistency with the other
    #     admin views.
    #     """
    #     return JavaScriptCatalog.as_view(packages=['django.contrib.admin'])(request)

    # @never_cache
    # def logout(self, request, extra_context=None):
    #     """
    #     Log out the user for the given HttpRequest.
    #
    #     This should *not* assume the user is already logged in.
    #     """
    #     from django.contrib.auth.views import LogoutView
    #     defaults = {
    #         'extra_context': {
    #             **self.each_context(request),
    #             # Since the user isn't logged out at this point, the value of
    #             # has_permission must be overridden.
    #             'has_permission': False,
    #             **(extra_context or {})
    #         },
    #     }
    #     if self.logout_template is not None:
    #         defaults['template_name'] = self.logout_template
    #     request.current_app = self.name
    #     return LogoutView.as_view(**defaults)(request)
    #
    # @never_cache
    # def login(self, request, extra_context=None):
    #     """
    #     Display the login form for the given HttpRequest.
    #     """
    #     if request.method == 'GET' and self.has_permission(request):
    #         # Already logged-in, redirect to admin index
    #         index_path = reverse('admin:index', current_app=self.name)
    #         return HttpResponseRedirect(index_path)
    #
    #     from django.contrib.auth.views import LoginView
    #     # Since this module gets imported in the application's root package,
    #     # it cannot import models from other applications at the module level,
    #     # and django.contrib.admin.forms eventually imports User.
    #     from django.contrib.admin.forms import AdminAuthenticationForm
    #     context = {
    #         **self.each_context(request),
    #         'title': _('Log in'),
    #         'app_path': request.get_full_path(),
    #         'username': request.user.get_username(),
    #     }
    #     if (REDIRECT_FIELD_NAME not in request.GET and
    #             REDIRECT_FIELD_NAME not in request.POST):
    #         context[REDIRECT_FIELD_NAME] = reverse('admin:index', current_app=self.name)
    #     context.update(extra_context or {})
    #
    #     defaults = {
    #         'extra_context': context,
    #         'authentication_form': self.login_form or AdminAuthenticationForm,
    #         'template_name': self.login_template or 'admin/login.html',
    #     }
    #     request.current_app = self.name
    #     return LoginView.as_view(**defaults)(request)

    def _build_app_dict(self, request, label=None):
        """
        Build the app dictionary. The optional `label` parameter filters models
        of a specific app.
        """
        app_dict = {}

        if label:
            models = {
                m: m_a for m, m_a in self._registry.items()
                if m._meta.app_label == label
            }
        else:
            models = self._registry

        for model, model_admin in models.items():
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
                    model_dict['admin_url'] = reverse('admin:%s_%s_changelist' % info, current_app=self.name)
                except NoReverseMatch:
                    pass
            if perms.get('add'):
                try:
                    model_dict['add_url'] = reverse('admin:%s_%s_add' % info, current_app=self.name)
                except NoReverseMatch:
                    pass

            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
            else:
                app_dict[app_label] = {
                    'name': apps.get_app_config(app_label).verbose_name,
                    'app_label': app_label,
                    'app_url': reverse(
                        'admin:app_list',
                        kwargs={'app_label': app_label},
                        current_app=self.name,
                    ),
                    'has_module_perms': has_module_perms,
                    'models': [model_dict],
                }

        if label:
            return app_dict.get(label)
        return app_dict

    def get_app_list(self, request):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request)

        # Sort the apps alphabetically.
        app_list = sorted(app_dict.values(), key=lambda x: x['name'].lower())

        # Sort the models alphabetically within each app.
        for app in app_list:
            app['models'].sort(key=lambda x: x['name'])

        return app_list

    @never_cache
    def index(self, request, extra_context=None):
        """
        Display the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        app_list = self.get_app_list(request)

        context = {
            **self.each_context(request),
            'title': self.index_title,
            'app_list': app_list,
            **(extra_context or {}),
        }

        request.current_app = self.name

        return TemplateResponse(request, self.index_template or 'custom_admin/index.html', context)

    def app_index(self, request, app_label, extra_context=None):
        app_dict = self._build_app_dict(request, app_label)
        if not app_dict:
            raise Http404('The requested admin page does not exist.')
        # Sort the models alphabetically within each app.
        app_dict['models'].sort(key=lambda x: x['name'])
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
