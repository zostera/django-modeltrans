from modeltrans.forms import TranslationModelForm

from .models import Blog


class BlogForm(TranslationModelForm):
    class Meta:
        model = Blog
        fields = ('title_nl', 'body')
