from django import forms
import re
from .models import CustomerReview, ShippingInformation, ContactWithUs, ScheduledMessage

class ProductReviewForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'placeholder': 'Write your comment here...',
                'class': 'form-control',
                'oninput': 'validateReviewText(this)'  # Add client-side validation
            }
        )
    )

    class Meta:
        model = CustomerReview
        fields = ('rating', 'name', 'comment',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add bootstrap classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Add HTML5 pattern validation for name field
        self.fields['name'].widget.attrs.update({
            'pattern': '[A-Za-z\u0980-\u09FF\\s]+',
            'title': 'Only Bangla and English letters are allowed (no numbers or special characters).'
        })

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')
        # Allow English letters, Bangla letters, and spaces only
        if not re.match(r'^[A-Za-z\u0980-\u09FF\s]+$', comment):
            raise forms.ValidationError(
                "Only Bangla and English letters are allowed (no numbers or special characters)."
            )
        return comment
    
class ShippingInformationForm(forms.ModelForm):
    class Meta:
        model = ShippingInformation
        fields = ('full_name', 'email', 'phone', 'city', 'address', 'special_note', 'delivery_location',)

class ContactWithUsForm(forms.ModelForm):
    class Meta:
        model = ContactWithUs
        fields = ('name', 'email', 'phone', 'message',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs) 
        self.fields['message'].widget.attrs = {'rows': 3}


class ScheduledMessageForm(forms.ModelForm):
    class Meta:
        model = ScheduledMessage
        fields = ['message', 'scheduled_time', 'send_to_all', 'phone_numbers']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }

    