from django import forms
from .models import Course, Module, Lesson, Resource, Review

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title','category','description','short_description','thumbnail','preview_video',
                  'level','language','price_type','price','discount_price','requirements','what_you_learn','tags','certificate_available']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control','placeholder':'Course Title'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':5}),
            'short_description': forms.TextInput(attrs={'class':'form-control'}),
            'category': forms.Select(attrs={'class':'form-select'}),
            'level': forms.Select(attrs={'class':'form-select'}),
            'language': forms.TextInput(attrs={'class':'form-control'}),
            'price_type': forms.Select(attrs={'class':'form-select'}),
            'price': forms.NumberInput(attrs={'class':'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class':'form-control'}),
            'requirements': forms.Textarea(attrs={'class':'form-control','rows':4,'placeholder':'One per line'}),
            'what_you_learn': forms.Textarea(attrs={'class':'form-control','rows':4,'placeholder':'One per line'}),
            'tags': forms.TextInput(attrs={'class':'form-control','placeholder':'Comma separated tags'}),
            'thumbnail': forms.FileInput(attrs={'class':'form-control'}),
            'preview_video': forms.FileInput(attrs={'class':'form-control'}),
            'certificate_available': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title','description','order']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'order': forms.NumberInput(attrs={'class':'form-control'}),
        }

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title','content_type','video','video_url','pdf','text_content','duration','order','is_preview']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'content_type': forms.Select(attrs={'class':'form-select'}),
            'video': forms.FileInput(attrs={'class':'form-control'}),
            'video_url': forms.URLInput(attrs={'class':'form-control','placeholder':'YouTube/Vimeo URL'}),
            'pdf': forms.FileInput(attrs={'class':'form-control'}),
            'text_content': forms.Textarea(attrs={'class':'form-control','rows':6}),
            'duration': forms.NumberInput(attrs={'class':'form-control'}),
            'order': forms.NumberInput(attrs={'class':'form-control'}),
            'is_preview': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating','comment']
        widgets = {
            'rating': forms.Select(attrs={'class':'form-select'}),
            'comment': forms.Textarea(attrs={'class':'form-control','rows':4,'placeholder':'Share your experience...'}),
        }
