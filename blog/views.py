from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext

from blog.models import User, Blog, Post, Tag
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

    if 'tagsearch' in request.GET:
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

@login_required
def blog_edit_old(request, blog_id):

    print 'Editing blog_id: %s' % (blog_id)

    action = 'Add'

    # for arg in request.POST:
    #     print '%s: %s' % (arg, request.POST[arg])

    from datetime import datetime
    from cgi import escape  # Used for escaping HTML before stored in the db

    if 'Go' in request.POST:

        u = User.objects.get(username__exact='jerrell')
        b = Blog.objects.get(name='General')

        tags = [tag.strip() for tag in request.POST['tags'].split(',') if tag.strip() != '']

        # Convert the input date from 'MM-DD-YYYY' format to PostgreSQL's date format
        ddate = datetime.strptime(request.POST['date'], '%m-%d-%Y').strftime('%Y-%m-%d %H:%M')
        print "date is %s" % (ddate)

        if blog_id:  # If we have a blog_id, then we want to either edit or delete
            if request.POST['Go'] == 'Delete':
                e = Post.objects.get(id=blog_id)
                e.delete()
                return blog_list(request, None)
            else:
                e = Post.objects.get(id=blog_id)
                e.title = request.POST['title']
                e.post = escape(request.POST['post'])
                e.date = ddate
                e.tags.clear()  # Remove all existing tags from the post
                e.save()
        else:   # Add post
            e = Post(user=u, blog=b, title=request.POST['title'], post=escape(request.POST['post']), date=str(ddate))
            e.date = ddate
            e.save()

        for tag in tags:
            newtag, __ = Tag.objects.get_or_create(name=tag)
            e.tags.add(newtag)

    tag_list = ''

    if blog_id:
        import HTMLParser
        blog_info = Post.objects.get(id=blog_id)
        blog_info.post = HTMLParser.HTMLParser().unescape(blog_info.post)
        action = 'Edit'
        print "Edit blog_id: %s, title: %s" % (blog_id, blog_info.title)
    else:
        blog_info = { "date": datetime.now()}  # For new posts, set the default date to now

    return render_to_response('blog/edit.html',
                              {'section': section, 'action': action, 'blog_info': blog_info, 'tags': tag_list },
                              context_instance=RequestContext(request))


@login_required
def tag_search(request):

    import json

    tags = [ tag.name for tag in Tag.objects.filter(name__istartswith=request.GET.get('query', '')) ]
    json_text = json.dumps(tags)

    return render_to_response('blog/tag_search.json',
                              {'section': section, 'info': json_text},
                              context_instance=RequestContext(request),
                              mimetype="application/json")
