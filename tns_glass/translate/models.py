from modeltranslation.translator import translator
from django.conf import settings

def get_class( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m

def get_translatable_models():
    """
    Returns a list of all the model classes which have translated fields on them
    """
    exclude_models = [get_class(clazz) for clazz in settings.EXCLUDED_TRANSLATE_MODELS]

    models = []
    for model in translator._registry.keys():
        if model not in exclude_models:
            models.append(model)

    # order our models by the type of the verbose name
    def name(model):
        return model._meta.verbose_name.lower()

    models.sort(key=name)
    return models

def get_foreign_languages():
    """
    What languages are installed in the system
    """
    return settings.LANGUAGES[1:]

def get_language_name(code):
    languages = get_foreign_languages()
    for lang in languages:
        if lang[0] == code:
            return lang[1]

class TranslationRecord:
    """
    Struct for passing around an object/field pairing
    """
    def __init__(self, obj, field, code):
        self.object = obj
        self.key = "%s__%s__%d" % (obj._meta.module_name, field, obj.id)
        self.type = obj._meta.verbose_name.title()
        self.field = field
        self.translated_field = "%s_%s" % (field, code)

        self.original = getattr(obj, 'description', getattr(obj, field))
        self.translated = getattr(obj, self.translated_field)

def get_translatable_records(code, translated=None):
    """
    Returns all the objects for the passed in language that can be translated
    """
    records = []
    for model in get_translatable_models():
        options = translator.get_options_for_model(model)
    
        # build a keyword dict for our filter based on the fields of the model
        kwargs = dict()
        for field in options.fields:
            if translated is None:
                objects = model.objects.all().order_by(field)
            else:
                kwargs["%s_%s__isnull" % (field, code)] = not translated
                objects = model.objects.filter(**kwargs).order_by(field)

            for obj in objects:
                records.append(TranslationRecord(obj, field, code))

    return records

class TranslationStats:
    """
    Simple struct for passing around translation statistics.
    """

    def __init__(self, code, total, translated):
        self.code = code
        self.language = get_language_name(code)
        self.total = total
        self.translated = translated

        
    def progress(self):
        if self.total == 0:
            return 0
        else:
            return (self.translated*100)/self.total

def get_translation_stats(lang, model=None):
    """
    Returns statistics on the total number of translatable items for the passed in
    class along with how many actually have translations
    """
    total = 0
    translated = 0

    # no model passed in, figure out our totals from the translated models
    if model == None:
        for model in get_translatable_models():
            stats = get_translation_stats(lang, model)
            total += stats.total
            translated += stats.translated

    # otherwise, figure out the stats just for the passed in model
    else:
        options = translator.get_options_for_model(model)
    
        # total # of items is the total count of active objects
        total = model.objects.count()

        # translated is number that have a value for the translated field
        kwargs = dict()
        for field in options.fields:
            kwargs["%s_%s__isnull" % (field, lang)] = False

            translated = model.objects.filter(**kwargs).count()

    return TranslationStats(lang, total, translated)

# monkey patch the permissions for rosetta, so that only users
# with country_translate can access the rosetta pages
def has_translate_permission(user):
    return user.has_perm('locales.country_translate')

from rosetta import views
views.can_translate = has_translate_permission


