import uuid
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from orders.models import Order, OrderProduct, Payment
from store.models import Product
from .forms import OrderForm
from carts.models import CartItem
import datetime
import stripe
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string



stripe.api_key = settings.STRIPE_SECRET_KEY
from django.http import Http404

def payments(request, order_number):
    current_user = request.user
    try:
        order = get_object_or_404(Order, user=current_user, is_ordered=False, order_number=order_number)
    except Http404:
        return HttpResponse("Order does not exist.", status=404)
    
    # Calculate total, tax, and grand total
    cart_items = CartItem.objects.filter(user=current_user)
    total = 0
    quantity = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == "POST":
        # Generate a unique payment ID
        payment_id = uuid.uuid4().hex
        # Create a Payment instance
        payment = Payment(
            user=current_user,
            payment_id=payment_id,
            payment_method='Stripe',
            amount_paid=str(grand_total),
            status='COMPLETED',
        )
        payment.save()
        order.payment = payment
        order.is_ordered = True
        order.save()

        # Save each item in the cart as an OrderProduct
        for item in cart_items:
            order_product = OrderProduct()
            order_product.order_id = order.id
            order_product.payment = payment
            order_product.user_id = request.user.id
            order_product.product_id = item.product_id
            order_product.quantity = item.quantity
            order_product.product_price = item.product.price
            order_product.ordered = True

            # Get the variations and set them for the order product
            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variations.all()

            # Save the order product before setting variations to avoid IntegrityError
            order_product.save()
            if product_variation.exists():
                order_product.variations.set(product_variation)
                order_product.save()  # Save again with variations

            # Reduce the quantity of the sold products
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

        # Clear the cart after placing the order
        CartItem.objects.filter(user=request.user).delete()
        
        #  Send Order recieved Email to customer
        mail_subject="Thank You for your order! "
        message = render_to_string("orders/order_recieved_email.html",{
            'user' : request.user,
            'order' : order,
            
        })
        to_email=request.user.email
        email_from=settings.EMAIL_HOST_USER
        send_email=EmailMessage(mail_subject,message,email_from,to=[to_email])
        
        send_email.send()         
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Total',
                    },
                    'unit_amount': int(grand_total * 100),  # Stripe expects the amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            
            success_url=request.build_absolute_uri(reverse('order_complete') + f'?order_number={order_number}&payment_id={payment_id}'),
            cancel_url=request.build_absolute_uri('/orders/cancel/'),
        )

        return redirect(session.url, code=303)
    else:
        return redirect('store')  # Redirect to store if not a POST request

def place_order(request, total=0, quantity=0):
    current_user = request.user
    
    # If the cart count is less than or equal to 0, redirect back to Shop
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    tax = 0
    grand_total = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax
    
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.email = form.cleaned_data['email']
            data.phone = form.cleaned_data['phone']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.city = form.cleaned_data['city']
            data.state = form.cleaned_data['state']
            data.country = form.cleaned_data['country']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()
            
            # Generate Order Number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime('%Y%m%d')
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            
            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order_number': order_number,
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
    else:
        form = OrderForm()

    return render(request, 'store/checkout.html')


def order_complete(request):
    order_number = request.GET.get('order_number')
    payment_id = request.GET.get('payment_id')
    try:
        # Retrieve the order matching the order number and payment ID
        order = Order.objects.get(order_number=order_number, payment__payment_id=payment_id)
        payment = get_object_or_404(Payment, payment_id=payment_id)
        
        # Ensure the payment belongs to the order
        if order.payment != payment:
            return HttpResponse("Order and payment do not match.")
        ordered_products = OrderProduct.objects.filter(order_id=order.id)
        
        grand_total = order.order_total + order.tax
        context = {
            'order': order,
            'ordered_products': ordered_products,
            'payment': payment,
            'grand_total':grand_total
        }        
        return render(request, 'orders/order_complete.html', context)
    except Order.DoesNotExist:
        return HttpResponse("Order does not exist.")
    except Order.MultipleObjectsReturned:
        return HttpResponse("Multiple orders found with the same order number and payment ID.")

    
    
    