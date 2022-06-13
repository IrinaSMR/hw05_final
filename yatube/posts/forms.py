from django.core.exceptions import ValidationError
from django.forms import ModelForm
from pytils.translit import slugify

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {'group': 'Группа', 'text': 'Текст'}
        help_texts = {'text': ('Обязательное поле для заполнения')}

    def clean_slug(self):
        """Обрабатывает случай, если slug не уникален."""
        cleaned_data = super().clean()
        slug = cleaned_data.get('slug')
        if not slug:
            title = cleaned_data.get('title')
            slug = slugify(title)[:100]
        if Post.objects.filter(slug=slug).exists():
            raise ValidationError(
                f'Адрес "{slug}" уже существует, '
                'придумайте уникальное значение'
            )
        return slug

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}        
