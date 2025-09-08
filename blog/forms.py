from django import forms
from .models import BlogComment

class CommentForm(forms.ModelForm):
    guest_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Your name (optional)'})
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comment here...'})
    )

    class Meta:
        model = BlogComment
        fields = ['comment', 'guest_name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            self.fields['guest_name'].widget = forms.HiddenInput()

class ReplyForm(forms.ModelForm):
    guest_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Your name (optional)'})
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write your reply here...'})
    )

    class Meta:
        model = BlogComment
        fields = ['comment', 'guest_name']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user and self.user.is_authenticated:
            self.fields['guest_name'].widget = forms.HiddenInput()