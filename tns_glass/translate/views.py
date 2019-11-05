from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import permission_required
from django.contrib import messages
from rosetta.views import list_languages
from .models import *

@permission_required('locales.country_translate')
def db(request, code):
    context = dict(code=code, language=get_language_name(code))

    translated = None
    filter_param = 'all'
    if 'filter' in request.REQUEST:
        filter_param = request.REQUEST['filter']
        if filter_param == 'translated':
            translated = True
        elif filter_param == 'untranslated':
            translated = False
        else:
            filter_param = 'all'

    context['filter'] = filter_param
    records = get_translatable_records(code, translated=translated)

    # they are updating translations
    if request.POST:
        # for each key they submitted
        for key in request.POST:
            # search for the matching record
            for record in records:
                if record.key == key:
                    # and update the translation
                    setattr(record.object, record.translated_field, request.POST[key])
                    record.translated = request.POST[key]
                    record.object.save()

        messages.success(request, "Your translations have been saved.")

    page = 1
    if 'page' in request.REQUEST:
        page = request.REQUEST['page']

    paginator = Paginator(records, 10)
    page = paginator.page(page)

    context['page_obj' ] = page
    context['paginator'] = paginator
    return render_to_response('translate/db.html', context, context_instance=RequestContext(request))        

@permission_required('locales.country_translate')
def index(request):
    """
    Wrapper around rosetta index 
    """
    context = dict()
    response =  list_languages(request)

    context['rosetta'] = response.content

    languages = get_foreign_languages()
    stats = [get_translation_stats(lang[0]) for lang in languages]
    context['stats'] = stats

    return render_to_response('translate/index.html', context, context_instance=RequestContext(request))    
