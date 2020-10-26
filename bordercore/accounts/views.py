import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView

from accounts.forms import UserProfileForm
from accounts.models import SortOrderNote, UserProfile
from blob.models import Blob

SECTION = 'prefs'


@method_decorator(login_required, name='dispatch')
class UserProfileDetailView(UpdateView):
    template_name = 'prefs/index.html'
    form_class = UserProfileForm

    def get(self, request, **kwargs):
        self.object = UserProfile.objects.get(user=self.request.user)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object, form=form)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super(UserProfileDetailView, self).get_context_data(**kwargs)
        context['groups'] = ', '.join([x.name for x in self.request.user.groups.all()])
        context['section'] = SECTION
        context['nav'] = 'prefs'
        context['title'] = 'Preferences'
        context['tags'] = [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in self.object.favorite_tags.all()]
        return context

    def get_object(self, queryset=None):
        obj = UserProfile.objects.get(user=self.request.user)
        return obj

    def form_valid(self, form):
        self.object = form.save()
        context = self.get_context_data(form=form)
        context["message"] = "Preferences updated"
        return self.render_to_response(context)

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(UserProfileDetailView, self).dispatch(*args, **kwargs)


@login_required
def sort_favorite_notes(request):
    """
    Move a given tag to a new position in a sorted list
    """

    note_uuid = request.POST["note_uuid"]
    new_position = int(request.POST["new_position"])

    note = Blob.objects.get(user=request.user, uuid=note_uuid)

    SortOrderNote.reorder(request.user, note.id, new_position)

    return HttpResponse(json.dumps("OK"), content_type="application/json")


@login_required
def add_to_favorites(request, uuid):

    note = Blob.objects.get(user=request.user, uuid=uuid)

    if note.is_favorite_note():
        messages.add_message(request, messages.WARNING, "This is already a favorite")
    else:
        sort_order = SortOrderNote(user_profile=request.user.userprofile, note=note)
        sort_order.save()
        messages.add_message(request, messages.WARNING, "Added to favorites")

    return HttpResponseRedirect(reverse('blob_detail', args=(uuid,)))


@login_required
def remove_from_favorites(request, uuid):

    note = Blob.objects.get(user=request.user, uuid=uuid)

    if not note.is_favorite_note():
        messages.add_message(request, messages.WARNING, "This is not a favorite")
    else:
        sort_order = SortOrderNote.objects.get(user_profile=request.user.userprofile, note=note)
        sort_order.delete()
        messages.add_message(request, messages.WARNING, "Removed from favorites")

    return HttpResponseRedirect(reverse('blob_detail', args=(uuid,)))


@login_required
def store_in_session(request):

    for key in request.POST:
        request.session[key] = request.POST[key]
    return JsonResponse({"status": "OK"}, safe=False)


def bc_login(request):

    message = ''

    if request.POST.get('username'):
        username = request.POST['username']
        password = request.POST['password']

        if not User.objects.filter(username=username).count():
            message = 'Username does not exist'
        else:

            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    response = redirect(request.POST.get("next", "homepage"))
                    # Remember the username for a month
                    response.set_cookie('bordercore_username', username, max_age=2592000)
                    return response
                    # Redirect to a success page.
                else:
                    message = 'Disabled account'
                    # Return a 'disabled account' error message
            else:
                message = 'Invalid login'
                # Return an 'invalid login' error message.

    return render(request, 'login.html', {
        'message': message,
        'next': request.GET.get('next')
    })


@login_required
def bc_logout(request):
    logout(request)
    return redirect('login')
