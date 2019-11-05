from django.forms import ModelChoiceField

class TreeModelChoiceField(ModelChoiceField):
    """
    Model choice field that looks for a 'depth' attribute and 'indents' the label
    for the field appropriately based on it

    We pass in a 'method' instead of a list because Django caches forms, so that method
    has to be exected every time 'all' is called
    """
    def __init__(self, model, method, **kwargs):

        class MethodWrapper:
            def __init__(self, model, method):
                self.model = model
                self.method = method

            def all(self):
                return self.method()

            def get(self, **kwargs):
                return model.objects.get(**kwargs)

        super(TreeModelChoiceField, self).__init__(MethodWrapper(model, method), **kwargs)

    def label_from_instance(self, obj):
        depth = getattr(obj, 'depth', 0)
        return depth * '--' + ' ' + str(obj)
