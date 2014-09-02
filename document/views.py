from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render_to_response

from document.models import Document
from document.forms import DocumentForm
from tag.models import Tag
from django.template import RequestContext

section = 'Documents'

@login_required
def document_edit(request, document_id):

    action = 'Edit'

    p = Document.objects.get(pk=document_id) if document_id else None

    if request.method == 'POST':

        if request.POST['Go'] in ['Edit', 'Add']:
            form = DocumentForm(request.POST, instance=p) # A form bound to the POST data
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m() # Save the many-to-many data for the form.
                messages.add_message(request, messages.INFO, 'Document edited')
                return document_detail(request, newform.id)
        elif request.POST['Go'] == 'Delete':
            p.delete()
            messages.add_message(request, messages.INFO, 'Document deleted')
#            return document_list(request, None)

    elif document_id:
        action = 'Edit'
        form = DocumentForm(instance=p)

    else:
        action = 'Add'
        form = DocumentForm() # An unbound form

    return render_to_response('kb/documents/edit.html',
                              {'section': section, 'action': action, 'form': form },
                              context_instance=RequestContext(request))


@login_required
def document_detail(request, document_id):

    d = Document.objects.get(pk=document_id)

    d.authors = ', '.join(d.author)
    d.content = d.content.replace('\n', '<br/>')

    return render_to_response('kb/documents/view.html',
                              { 'document': d },
                              context_instance=RequestContext(request))
