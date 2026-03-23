from django import forms
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Post, Comment, CustomUser


def validate_image_size(image):
    file_size = image.size
    limit_mb = getattr(settings, 'MAX_IMAGE_SIZE', 5 * 1024 * 1024)
    if file_size > limit_mb:
        raise ValidationError(f"Image size should not exceed {limit_mb // (1024 * 1024)}MB.")


def validate_image_extension(image):
    import os
    ext = os.path.splitext(image.name)[1].lower()
    valid_extensions = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
    if ext not in valid_extensions:
        raise ValidationError(f"Unsupported file extension. Allowed: {', '.join(valid_extensions)}")


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'category', 'featured_image', 'excerpt', 'content', 'tags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mdc-text-field__input',
                'placeholder': 'Enter post title',
            }),
            'category': forms.Select(attrs={
                'class': 'mdc-select__native-control',
            }),
            'excerpt': forms.Textarea(attrs={
                'class': 'mdc-text-field__input',
                'rows': 3,
                'placeholder': 'Brief summary of your post',
            }),
            'content': forms.Textarea(attrs={
                'class': 'markdown-editor',
                'rows': 15,
                'placeholder': 'Write your content here using Markdown...',
            }),
            'status': forms.Select(attrs={
                'class': 'mdc-select__native-control',
            }),
            'tags': forms.TextInput(attrs={
                'class': 'tag-input',
                'data-role': 'tagsinput',
                'placeholder': 'Add tags (press Enter)',
            }),
        }
    
    featured_image = forms.ImageField(
        required=False,
        validators=[validate_image_size, validate_image_extension],
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': 'image/*',
        })
    )
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            if len(title) < 10:
                raise ValidationError("Title must be at least 10 characters long.")
            if len(title) > 200:
                raise ValidationError("Title must not exceed 200 characters.")
        return title
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content:
            if len(content) < 50:
                raise ValidationError("Content must be at least 50 characters long.")
        return content


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'mdc-text-field__input comment-input',
                'rows': 3,
                'placeholder': 'Write your comment...',
            }),
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if content:
            if len(content) < 5:
                raise ValidationError("Comment must be at least 5 characters long.")
            if len(content) > 2000:
                raise ValidationError("Comment must not exceed 2000 characters.")
        return content


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_picture', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'mdc-text-field__input',
                'rows': 4,
            }),
        }
    
    profile_picture = forms.ImageField(
        required=False,
        validators=[validate_image_size, validate_image_extension],
        widget=forms.FileInput(attrs={
            'class': 'file-input',
            'accept': 'image/*',
        })
    )


class SearchForm(forms.Form):
    q = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'search-input',
            'placeholder': 'Search posts...',
            'hx-get': '/search/',
            'hx-trigger': 'keyup changed delay:300ms',
            'hx-target': '#search-results',
            'hx-swap': 'innerHTML',
        })
    )
