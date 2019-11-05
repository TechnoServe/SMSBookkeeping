from smartmin.views import *
from .models import Grade
from util.fields import TreeModelChoiceField
from django.utils.translation import ugettext_lazy as _

class GradeForm(forms.ModelForm):
    parent = TreeModelChoiceField(Grade, Grade.get_possible_parent_grades, required=False)

    def clean_parent(self):
        """
        Validates that the parent set is valid
        """
        value = self.cleaned_data['parent']

        if value:
            # check self parenting
            if value == self.instance:
                raise forms.ValidationError(_("Grade cannot be the parent of itself"))

            # check parent of a child
            parent = value.parent
            while parent:
                if parent == self.instance:
                    raise forms.ValidationError(_("Grade cannot have one of its children as its parent"))
                parent = parent.parent

        return value

    def clean_kind(self):
        """
        Validates that the user doesn't set the grade kind to something different than it's parent
        """
        value = self.cleaned_data['kind']
        
        if 'parent' in self.cleaned_data and self.cleaned_data['parent']:
            parent = self.cleaned_data['parent']
            if parent.kind != value:
                raise forms.ValidationError(_("Grade kind must agree with parent"))

        return value

    class Meta:
        model = Grade

class GradeCRUDL(SmartCRUDL):
    model = Grade
    actions = ('create', 'update', 'list')
    permissions = True

    class Create(SmartCreateView):
        form_class = GradeForm
        fields = ('parent', 'name', 'kind', 'is_not_processed', 'include_in_credit_report', 'order')

    class Update(SmartUpdateView):
        form_class = GradeForm
        fields = ('is_active', 'parent', 'name', 'kind', 'is_not_processed', 'include_in_credit_report', 'order')

    class List(SmartListView):
        fields = ('name', 'parent', 'include_in_credit_report')

        def get_context_data(self, *args, **kwargs):
            context = super(GradeCRUDL.List, self).get_context_data(*args, **kwargs)
            context['sorted_grades'] = Grade.get_grade_tree()
            return context
