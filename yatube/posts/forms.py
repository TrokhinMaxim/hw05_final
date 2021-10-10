from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

        def clean_data(self):
            data = self.cleaned_data['text']
            if data == data:
                raise forms.ValidationError('Тут пусто!')
            return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', 'post')
