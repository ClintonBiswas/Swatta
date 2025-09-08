from django import forms
from .models import CustomerReview, ShippingInformation, ContactWithUs, ScheduledMessage

class ProductReviewForm(forms.ModelForm):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your comment here...'})
    )
    class Meta:
        model = CustomerReview
        fields = ('rating', 'name', 'comment',)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

    