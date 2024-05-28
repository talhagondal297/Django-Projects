from django.http import HttpResponse
from django.shortcuts import render 
from store.models import Product, ReviewRating

def home(request):
    products = Product.objects.all().filter(is_available=True).order_by('-created_date')
    reviews_dict = {}

    # Get the reviews for each product
    for product in products:
        reviews = ReviewRating.objects.filter(product_id=product.id, status=True)
        reviews_dict[product.id] = reviews

    context = {
        'products': products,
        'reviews_dict': reviews_dict
    }
    return render(request, 'home.html', context)
