# from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from carts.models import Cart, CartItem
from carts.views import _cart_id
from orders.models import Order, OrderProduct
from .forms import RegistrationForm, LoginForm, ResetForm,ForgotPasswordForm, UserForm, UserProfileForm
from .models import Account, UserProfile
from django.contrib import messages,auth
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
# from store.views import _cartid
# from store.models import CartModel,CartItemModel
import requests


# email avtivation
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage
from django.conf import settings


# Create your views here.

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Process the valid form data and create a user
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            phone_number = form.cleaned_data["phone_number"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]
            username = email.split("@")[0]

            user = Account.objects.create_user(first_name=first_name, last_name=last_name, username=username, email=email, password=password)
            user.phone_number = phone_number
            user.save()
           
            #user email activation
            current_site=get_current_site(request)
            mail_subject="Please Acvtivate Your Account"
            message=render_to_string("accounts/account_email_verification.html",{
                "user":user,
                "domain":current_site,
                "uid":urlsafe_base64_encode(force_bytes(user.pk)),
                "token":default_token_generator.make_token(user)
            })
            email_to=[email]
            email_from=settings.EMAIL_HOST_USER
            send_email=EmailMessage(mail_subject,message,email_from,email_to)
            
            send_email.send() 
            
            # messages.success(request, f"Verification email has been sent to {email} please verify through your email")
            
            # Redirect to a success page or login page, for example
            return redirect(f'/accounts/login/?command=verification&email={email}') # Replace with your desired URL

    else:
        form = RegistrationForm()

    context = {
        "form": form,
    }
    return render(request, "accounts/register.html", context)


def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user_password = form.cleaned_data["password"]
            user = auth.authenticate(email=email, password=user_password)
            
            if user is not None:
                try:
                    cart =Cart.objects.get(cart_id=_cart_id(request))
                    is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                    if is_cart_item_exists:
                        cart_item = CartItem.objects.filter(cart=cart)
                        
                        product_variation = []
                        for item in cart_item:
                            variation = item.variations.all()
                            product_variation.append(list(variation))
                            
                        # Get the cart items from the user to access his product variations
                        cart_item=CartItem.objects.filter(user=user) 
                        ex_var_list =[]
                        id =[]
                        for item in cart_item:
                            existing_variation = item.variations.all()
                            ex_var_list.append(list(existing_variation))
                            id.append(item.id)
                            
                        item_quantity = 0    
                        for pr in product_variation:
                            if pr in ex_var_list:
                                index = ex_var_list.index(pr)
                                item_id = id[index]
                                item= CartItem.objects.get(id=item_id)
                                item_quantity += 1
                                item.user = user
                                item.save()
                            else:
                                cart_item=CartItem.objects.filter(cart=cart)
                                for item in cart_item:
                                    item.user = user
                                    item.save()
                        
                except:
                    print("entering inside except block")
                    pass
                
                auth.login(request, user)
                messages.success(request, "You are logged in successfully")
                url = request.META.get('HTTP_REFERER')
                try:
                    query = requests.utils.urlparse(url).query
                    params = dict(x.split('=') for x in query.split('&'))
                    if 'next' in params:
                        nextpage = params['next']
                        return redirect(nextpage)
                except:
                    return redirect("dashboard")  # Redirect to a default page if 'next' is not present
            else:
                messages.error(request, "Invalid email or password")
        else:
            messages.error(request, "Invalid form data")
    else:
        form = LoginForm()

    context = {"form": form}
    return render(request, "accounts/login.html", context)




@login_required(login_url="login")
def logout(request):
    auth.logout(request)
    messages.success(request, "logout successfully")

    return redirect('login')  



def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated. You can now log in.')
        return redirect('login')  # Redirect to the login page
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        return redirect('register')  # Redirect to the login page with an error message

@login_required(login_url="login")
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user=request.user.id, is_ordered=True)
    orders_count = orders.count()
    userprofile =UserProfile.objects.get(user_id=request.user.id)
    
    context = {
        'orders_count': orders_count,
        'userprofile':userprofile,
    }
    return render(request, 'accounts/dashboard.html',context)


def forgot_password(request):
    form = LoginForm()

    if request.method == "POST":
        form = ResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            if Account.objects.filter(email=email).exists():
                user = Account.objects.get(email=email)

                # User email activation
                current_site = get_current_site(request)
                mail_subject = "Reset Your Password"
                message = render_to_string("accounts/reset_password_email.html", {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user)
                })
                email_to = [email]
                email_from = settings.EMAIL_HOST_USER
                send_email = EmailMessage(mail_subject, message, email_from, email_to)

                send_email.send()
                messages.success(request, f"Password reset email has been sent to {email}. Please reset your password through email.")
                
                # Redirect to a success page or login page, for example
                return redirect('login')  # Replace with your desired URL
            else:
                messages.error(request, "Account does not exist.")
                return redirect('forgot_password')
        else:
            messages.error(request, "Invalid information.")
    context = {"form": form}
    return render(request, "accounts/forgot_password.html", context)



def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid']=uid
        messages.success(request, 'please reset you password')
        return redirect("resetpassword")
    else:
        messages.error(request, 'link expired')
        return redirect("login")



def reset_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data["password"]
            confirm_password = form.cleaned_data["confirm_password"]
            if password==confirm_password:
                uid=request.session.get("uid")
                user=Account.objects.get(pk=uid)
                user.set_password(password)
                user.save()
            else:
                messages.error(request, 'Passwords do not match')
                return redirect("resetpassword")
                
            messages.success(request, 'Your password has reset successfully.')
            return redirect('login')  # Redirect to the login page after resetting the password
        else:
            messages.error(request, 'Invalid form data.')
    else:
        form = ForgotPasswordForm()
    context={"form":form}
    return render(request, "accounts/reset_password.html", context)


@login_required(login_url="login")
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context={
        "orders":orders
        }
    
    return render(request, 'accounts/my_orders.html', context)


@login_required(login_url="login")
def edit_profile(request):
    user = request.user
    userprofile = get_object_or_404(UserProfile, user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile has been updated")
            return redirect('edit_profile')
    else:
        user_form = UserForm(instance=user)
        profile_form = UserProfileForm(instance=userprofile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'userprofile':userprofile,
    }
    
    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url="login")
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__iexact=request.user.username)
        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.error(request, "Password Updated Successfully. ")
                return redirect('change_password')
        
            else:
                messages.error(request, "Please enter valid current password. ")
                return redirect('change_password')
        else:
                messages.error(request, "Password does not match! ")
                return redirect('change_password')
   
    return render(request, 'accounts/change_password.html')

@login_required(login_url="login")
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    quantity = 0
    total = 0
    tax = 0
    grand_total = 0
    for cart_item in order_detail:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax
    
    
    context={
        'order_detail':order_detail,
        'order':order,
        'grand_total':grand_total,
    }
    
    return render(request, 'accounts/order_detail.html',context)