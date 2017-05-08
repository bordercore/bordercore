import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic.edit import UpdateView

from accounts.forms import UserProfileForm
from accounts.models import UserProfile

SECTION = 'Prefs'


class UserProfileDetailView(UpdateView):
    template_name = 'prefs/index.html'
    form_class = UserProfileForm

    def get(self, request, **kwargs):
        self.object = UserProfile.objects.get(user=self.request.user)
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object, form=form)
        return self.render_to_response(context)

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


def store_in_session(request):

    for key in request.POST:
        request.session[key] = request.POST[key]
    return HttpResponse(json.dumps('OK'), content_type="application/json")


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
                    response = redirect('homepage')
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

    return render(request, 'login.html', {'message': message})


def bc_logout(request):
    logout(request)
    return redirect('login')
