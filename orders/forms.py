from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    transaction_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    class Meta:
        model = Order
        fields =['first_name', 'last_name','email','phone','address_line_1','address_line_2','city','state','country','order_note', 'transaction_id']
        