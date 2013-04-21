from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

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
                    return redirect('homepage')
                    # Redirect to a success page.
                else:
                    message = 'Disabled account'
                    # Return a 'disabled account' error message
            else:
                message = 'Invalid login'
                # Return an 'invalid login' error message.

    return render_to_response('login.html', { 'message': message },
                              context_instance=RequestContext(request))
