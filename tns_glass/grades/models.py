from django.db import models
from smartmin.models import SmartModel
from django.utils.translation import ugettext_lazy as _

class Grade(SmartModel):
    KIND_CHOICES = (('CHE', _("Cherry")),
                    ('PAR', _("Parchment")),
                    ('GRE', _("Green")),
                    ('UNW', _("Unwashed Coffee")))

    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_("Parent"),
                               help_text=_("The parent, or category of this grade"))
    name = models.CharField(max_length=200, verbose_name=_("Name"),
                            help_text=_("The name of this grade, ie: Green 15+"))
    kind = models.CharField(max_length=3, choices=KIND_CHOICES, blank=False, null=False, verbose_name=_("Kind"), 
                            help_text=_("What kind of grade this is, child grades must be of the same kind as their parent"))
    is_not_processed = models.BooleanField(default=False,
                                           verbose_name=_("Not Processed Further"),
                                           help_text=_("Whether this grade does not undergo further processing, for example grades that are sold locally or are unwashed"))
    order = models.IntegerField(max_length=2, verbose_name=_("Order"),
                                help_text=_("The order this grade will be displayed in lists, smaller orders come first"))
    include_in_credit_report = models.BooleanField(default=False, verbose_name=_("Include in Credit Report"),
                                                   help_text=_("Whether to include this grade in the credit report"))

    def get_child_tree(self, **kwargs):
        return Grade.get_grade_tree(parent=self, **kwargs)

    def _full_name(self):
        """
        Returns the full name for a grade.  This includes the parent name
        """
        if self.parent:
            return "%s - %s" % (self.parent.full_name, self.name)
        else:
            return self.name

    full_name = property(_full_name)

    @classmethod
    def from_full_name(self, full_name):
        """
        Looks up a grade using its full name, that is for a grade named '13,14' under 'Green', the 
        full name is "Green - 13,14"

        This method looks that grade up by that name
        """
        full_name = full_name.lower().strip().replace(' ', '')
        for grade in Grade.objects.filter(is_active=True):
            if full_name == grade.full_name.lower().replace(' ', ''):
                return grade

        return None

    @classmethod
    def _add_children(cls, grades, parent, **kwargs):
        children = Grade.objects.filter(parent=parent, **kwargs)
        parent.has_children = len(children) > 0

        for child in children:
            child.depth = parent.depth + 1
            grades.append(child)
            Grade._add_children(grades, child, **kwargs)

    @classmethod
    def get_grade_tree(cls, parent=None, **kwargs):
        grade_tree = []
        grades = Grade.objects.filter(parent=parent, **kwargs)

        depth = 0
        if parent:
            depth = getattr(parent, 'depth', -1) + 1
            parent.has_children = len(grades) > 0

        for grade in grades:
            grade.depth = depth
            grade_tree.append(grade)
            Grade._add_children(grade_tree, grade, **kwargs)

        return grade_tree

    @classmethod
    def get_possible_parent_grades(cls, **kwargs):
        grade_tree = []
        grades = Grade.objects.filter(parent=None, **kwargs)

        for grade in grades:
            grade.depth = 0
            grade_tree.append(grade)

            for child in grade.children.all():
                child.depth = 1
                grade_tree.append(child)

        return grade_tree

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('order',)
        unique_together = ('parent', 'name')
