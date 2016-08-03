from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from document.models import Document
from document.forms import DocumentForm

section = 'Documents'


@login_required
def document_edit(request, document_id):

    action = 'Edit'

    p = Document.objects.get(pk=document_id) if document_id else None

    if request.method == 'POST':

        if request.POST['Go'] in ['Edit', 'Add']:
            form = DocumentForm(request.POST, instance=p)
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m()
                messages.add_message(request, messages.INFO, 'Document {}ed'.format(request.POST['Go'].lower()))
                return document_detail(request, newform.id)
        elif request.POST['Go'] == 'Delete':
            p.delete()
            messages.add_message(request, messages.INFO, 'Document deleted')
            form = DocumentForm()
            action = 'Add'

    elif document_id:
        action = 'Edit'
        form = DocumentForm(instance=p)

    else:
        action = 'Add'
        form = DocumentForm()

    return render(request, 'kb/documents/edit.html', {'section': section,
                                                      'action': action,
                                                      'form': form})


@login_required
def document_detail(request, document_id):

    d = Document.objects.get(pk=document_id)

    d.authors = ', '.join(d.author)

    return render(request, 'kb/documents/view.html', {'document': d})
