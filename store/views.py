from datetime import timezone
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from carts.models import CartItem
from carts.views import _cart_id
from orders.models import OrderProduct
from store.forms import ReviewForm
from store.models import Product, ProductGallery, ReviewRating
from category.models import Category
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
# Create your views here.
def store(request, category_slug = None):
    categories = None
    products = None
    
    if category_slug != None:
        categories = get_object_or_404(Category, slug = category_slug)
        products = Product.objects.filter(category = categories, is_available = True)
        paginator = Paginator(products, 1)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:
        products = Product.objects.all().filter(is_available = True).order_by('id')
        paginator = Paginator(products, 3)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
        
    context = {
        'products': paged_products ,
        'product_count': product_count
    }
    return render(request, 'store/store.html',context)


def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug = category_slug, slug = product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product= single_product).exists()
    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)

    orderproduct = None
    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product=single_product).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    
    #  Get the reviews
    reviews=ReviewRating.objects.filter(product_id = single_product.id, status=True)
    product_gallery = ProductGallery.objects.filter(product_id= single_product.id)
    
    context = {
        'single_product':single_product,
        'in_cart':in_cart,
        'orderproduct':orderproduct,
        'reviews':reviews,
        'product_gallery':product_gallery,
    }
    return render(request, 'store/product_detail.html',context)

def search(request):
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            products = Product.objects.order_by('-created_date').filter(Q(description__icontains = keyword) |  Q( product_name__icontains = keyword))
            product_count = products.count()
        context ={
            'products':products,
            'product_count':product_count,
        }
            
    return render(request, 'store/store.html',context)


@login_required(login_url="login")
def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    product = get_object_or_404(Product, id=product_id)
    if request.method == "POST":
        try:
            reviews=ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form=ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form=ReviewForm(request.POST)
            if form.is_valid():
                data=ReviewRating()
                data.user = request.user  # Set the user field
                data.product = product  # Set the product field
                data.subject=form.cleaned_data['subject']
                data.rating=form.cleaned_data['rating']
                data.review=form.cleaned_data['review']
                data.ip=request.META.get("REMOTE_ADDR")
                data.product_id = product_id
                
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
                
    return redirect(url)