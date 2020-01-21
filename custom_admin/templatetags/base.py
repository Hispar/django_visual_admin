from django.contrib.admin.templatetags.base import InclusionAdminNode as BaseInclusionAdminNode


class InclusionAdminNode(BaseInclusionAdminNode):
    """
    Template tag that allows its template to be overridden per model, per app,
    or globally.
    """

    def render(self, context):
        opts = context['opts']
        app_label = opts.app_label.lower()
        object_name = opts.object_name.lower()
        # Load template for this render call. (Setting self.filename isn't
        # thread-safe.)
        context.render_context[self] = context.template.engine.select_template([
            'admin/%s/%s/%s' % (app_label, object_name, self.template_name),
            'admin/%s/%s' % (app_label, self.template_name),
            'custom_admin/%s' % (self.template_name,),
            'admin/%s' % (self.template_name,),
        ])
        return super().render(context)
