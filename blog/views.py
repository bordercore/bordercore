from blog.models import User, Blog, Post, Tag
from django.contrib.auth.decorators import login_required
#from django.core.urlresolvers import reverse
#from django.http import HttpResponseRedirect, HttpResponse
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext

#from subprocess import call
section = 'Blog'

@login_required
def blog_list(request, blog_id):

    did_submit = False
    #    if not request.user.is_authenticated():
    #        return HttpResponseRedirect('/accounts/login/?next=%s' % request.path)
    message = ''
    results = ''
    #    request.session["fav_color"] = "blue"
    if not request.user.is_authenticated():
        message = 'User is NOT authenticated'
    else:
        message = 'Hello ' + request.user.username

    if 'tagsearch' in request.GET:
        posts = Post.objects.filter(tags__name__exact=request.GET['tagsearch']).order_by('-created')
    elif 'search_item' in request.GET:
        posts = Post.objects.filter(
            Q(post__icontains=request.GET['search_item']) |
            Q(title__icontains=request.GET['search_item'])
        )
    elif blog_id:
        posts = Post.objects.filter(id=blog_id)
    else:
        # posts = Post.objects.filter(id=1120)
        posts = Post.objects.order_by('-created').all()[:10]

    # pprint(posts)

    # if 'Go' in request.POST:
    #     did_submit = True
    #     mysolr = BCSolr()
    #     results = mysolr.search(request.POST['value'], "title")

    return render_to_response('blog/index.html',
                              {'section': section, 'posts': posts, 'message': message, 'results': results, 'did_submit': did_submit },
                              context_instance=RequestContext(request))


@login_required
def blog_edit(request, blog_id):

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
                print "Edit blog_id: %s" % (blog_id)
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
