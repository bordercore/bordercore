from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from book.models import Book

SECTION = 'Books'


@method_decorator(login_required, name='dispatch')
class BookListView(ListView):

    model = Book
    template_name = 'book/index.html'
    context_object_name = 'info'
    selected_letter = 'A'

    def get_queryset(self):
        if self.args[0]:
            self.selected_letter = self.args[0]

        return Book.objects.filter(user=self.request.user, title__istartswith=self.selected_letter)

    def get_context_data(self, **kwargs):
        context = super(BookListView, self).get_context_data(**kwargs)

        info = []

        for myobject in context['object_list']:
            info.append(dict(title=myobject.title, author=', '.join([author.name for author in myobject.author.all()]), year=myobject.year))

        import string
        context['alphabet'] = string.ascii_uppercase
        context['selected_letter'] = self.selected_letter
        context['cols'] = ['title', 'author', 'year']
        context['section'] = SECTION
        context['info'] = info
        return context
