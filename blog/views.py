from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext

from blog.models import Blog, Post
from blog.forms import BlogForm

section = 'Blog'
ITEMS_PER_PAGE = 10

@login_required
def blog_list(request, blog_id):

    message = ''
    show_pagination = True

    if not request.user.is_authenticated():
        message = 'User is NOT authenticated'
    else:
        message = 'Hello ' + request.user.username

    if request.GET.get('tagsearch', ''):
        post_list = Post.objects.filter(tags__name__exact=request.GET['tagsearch']).order_by('-created')
    elif 'search_item' in request.GET:
        post_list = Post.objects.filter(
            Q(post__icontains=request.GET['search_item']) |
            Q(title__icontains=request.GET['search_item'])
        )
    elif blog_id:
        post_list = Post.objects.filter(id=blog_id)
        show_pagination = False
    else:
        # posts = Post.objects.order_by('-created').all()[:ITEMS_PER_PAGE]
        post_list = Post.objects.order_by('-created').all()

    paginator = Paginator(post_list, ITEMS_PER_PAGE)

    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        posts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        posts = paginator.page(paginator.num_pages)

    return render_to_response('blog/index.html',
                              {'section': section, 'show_pagination': show_pagination, 'posts': posts, 'message': message },
                              context_instance=RequestContext(request))


@login_required
def blog_edit(request, post_id):

    action = 'Edit'

    p = Post.objects.get(pk=post_id) if post_id else None

    if request.method == 'POST':

        if request.POST['Go'] in ['Edit', 'Add']:
            form = BlogForm(request.POST, instance=p) # A form bound to the POST data
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.blog = Blog.objects.get(name='General')
                newform.save()
                form.save_m2m() # Save the many-to-many data for the form.
                messages.add_message(request, messages.INFO, 'Blog post edited')
                return blog_list(request, newform.id)
        elif request.POST['Go'] == 'Delete':
            p.delete()
            messages.add_message(request, messages.INFO, 'Blog post deleted')
            return blog_list(request, None)

    elif post_id:
        action = 'Edit'
        form = BlogForm(instance=p)

    else:
        action = 'Add'
        form = BlogForm() # An unbound form

    return render_to_response('blog/edit.html',
                              {'section': section, 'action': action, 'form': form },
                              context_instance=RequestContext(request))


# @login_required
# def tag_search(request):

#     import json

#     # Only retrieve tags which have been applied to at least one blog post

#     # Use this for the new Twitter typeahead
#     # tag_list = [{'value':x.name} for x in Tag.objects.filter(name__istartswith=request.GET.get('query', ''), post__isnull=False).distinct('name')]

#     # Use this for the typeahead included in Bootstrap 2
#     tag_list = [x.name for x in Tag.objects.filter(name__istartswith=request.GET.get('query', ''), post__isnull=False).distinct('name')]

#     return render_to_response('return_json.json',
#                               {'section': section, 'info': json.dumps(tag_list)},
#                               context_instance=RequestContext(request),
#                               content_type="application/json")
