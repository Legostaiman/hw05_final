from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['group',
                  'text',
                  'image']
        labels = {'group': 'Выберите группу',
                  'text': 'Текст',
                  'image': 'Прикрепите картинку к посту'}
        help_texts = {'text': 'Текст поста, если что...',
                      'group': 'Тут можно ничего не выбирать, если не хочется.'}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'текст комментария'}
