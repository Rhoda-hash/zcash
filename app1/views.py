from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login, logout
from .models import Customer, Transaction, Voucher

#CRUD : CREATE READ UPDATE DELETE
# Create your views here.
@login_required(login_url='/login/')
def homePage(request):
    user : User = request.user
    # show some of the details of the user in the dashboard and also show some of the transactions that they have done in the past
    if user.is_superuser :
        return redirect("/admin/")
    
    try :
        customer, was_created = Customer.objects.get_or_create(user=user)
        transactions = Transaction.objects.filter(sender=customer) | Transaction.objects.filter(receiver=customer)
        transactions = transactions.order_by('-date')[:5]
        return render(request,'dashboard.html',{"customer" : customer, "transactions": transactions})
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})
    
   
    # try :
    #     # customer = Customer.objects.create(user=user,balance=5000.00, pin='5645',gender='m')
    #     # customer.save()
    #     customer, was_created = Customer.objects.get_or_create(user=user)
    #     # get the first 5 transaction for the customer if any 
        
    #     return render(request,'dashboard.html',{"customer" : customer})
    # except Exception as e :
    #     return render(request,'404.html', {'error': str(e)})

@login_required(login_url='/login/')
def depositPage(request):
    user : User = request.user
    if user.is_superuser :
        return redirect("/admin/")
    try :
        customer = Customer.objects.get(user=user)
        if request.method == 'POST':
            voucher_code = request.POST.get('voucher_code')
            pin = request.POST.get('pin')
            confirmation_code = request.POST.get('confirmation_code')
            
            if not customer.confirmIfUserPinIsCorrect(pin):
                return render(request,'deposit.html',{'error': 'Incorrect PIN'})
            
            try:
                voucher = Voucher.objects.get(code=voucher_code, is_loaded=False)
                if voucher.customer != customer :
                    return render(request,'deposit.html',{'error':"Voucher to load must be yours!"})

            except Voucher.DoesNotExist:
                return render(request,'deposit.html',{'error': 'Invalid or already used voucher code'})
            
            if confirmation_code:
                # Check confirmation
                session_code = request.session.get('deposit_confirmation_code')
                if confirmation_code == session_code:
                    # Process deposit
                    customer.balance += voucher.amount
                    customer.save()
                    voucher.is_loaded = True
                    voucher.save()
                    # Clear session
                    del request.session['deposit_confirmation_code']

                    # document the transaction 
                    transaction = Transaction.objects.create(sender=customer,receiver=customer,amount=voucher.amount,transaction_type='deposit')
                    transaction.save()

                    return render(request,'deposit.html',{'success': f'Successfully deposited NGN{voucher.amount}'})
                else:
                    return render(request,'deposit.html',{'error': 'Incorrect confirmation code', 'show_confirmation': True, 'user_name': user.get_full_name() or user.username})
            else:
                # Generate confirmation code
                import random
                code = str(random.randint(100000, 999999))
                request.session['deposit_confirmation_code'] = code
                return render(request,'deposit.html',{'show_confirmation': True, 'confirmation_code': code, 'user_name': user.get_full_name() or user.username, 'voucher_code': voucher_code, 'pin': pin})
        
        return render(request,'deposit.html',{})
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})

@login_required(login_url='/login/')
def pinPage(request):
    user : User = request.user
    if user.is_superuser :
        return redirect("/admin/")
    try :
        customer = Customer.objects.get(user=user)
        pin_exist = True if customer.pin else False
 
        if request.method == 'POST':
            new_pin :str = request.POST.get("new_pin")
            confirm_pin :str = request.POST.get("confirm_pin")

            if len(new_pin) != 4 or len(confirm_pin) != 4 or not new_pin.isdigit or not confirm_pin.isdigit :
                error = ' pin must be a four digit number'
                return render(request,'pin.html',{'customer': customer,'pin_exist':pin_exist,'error':error})
            
            if new_pin != confirm_pin :
                error = 'pin must match before setting your pin'
                return render(request,'pin.html',{'customer': customer,'pin_exist':pin_exist,'error':error})
            
            if not pin_exist :
                # process a setting up a new pin from scratch for the user 
                customer.hashUserPin(new_pin)
                pin_exist = True 
                return render(request,'pin.html',{'customer': customer,'pin_exist':pin_exist,'success':'Pin set successfully'})
            
            # process at this point for  a user that is updating his pin
            # process .. retrieve the old_pin... confirm it is four digit, confirm it also with confirmIfUserPinIsCorrect ... and then if all okay process to hashUserPin and send right message
            old_pin :str = request.POST.get("old_pin")
                
            if len(old_pin) != 4 or len(new_pin) != 4 or len(confirm_pin) != 4 or not old_pin.isdigit or not new_pin.isdigit or not confirm_pin.isdigit :
                    error = 'old pin must be a four digit number'
                    return render(request,'pin.html',{'customer': customer,'pin_exist':pin_exist,'error':error})

            # confirm if the old pin is correct     
            if not customer.confirmIfUserPinIsCorrect(old_pin) :
                error = 'old pin is incorrect, please enter the correct old pin to update your pin'
                return render(request,'pin.html',{'customer': customer,'pin_exist':pin_exist,'error':error})
            
            customer.hashUserPin(new_pin)
            return render(request,'pin.html',{'customer': customer,'pin_exist':pin_exist,'success':'Pin updated successfully'})

        return render(request,'pin.html',{'customer': customer,'pin_exist':pin_exist})
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})

@login_required(login_url='/login/')
def transferPage(request):
    user : User = request.user
    if user.is_superuser :
        return redirect("/admin/")
    
    try :
        if request.method == 'POST':
            account_number = request.POST.get('account_number')
            amount = request.POST.get('amount')
            pin = request.POST.get('pin')
            if len(account_number) != 10 or not account_number.isdigit() :
                error = 'account number must be a 10 digit number'
                return render(request,'transfer.html',{'error':error})
            if len(amount) <= 0 or not amount.isdigit() :
                error = 'amount is not valid'
                return render(request,'transfer.html',{'error':error})
            if not pin.isdigit() or len(pin) != 4 :
                error = 'pin must be a four digit number'
                return render(request,'transfer.html',{'error':error})
            customer = Customer.objects.get(user=user)
            if customer.balance < float(amount) :
                error = 'insufficient balance for this transfer'
                return render(request,'transfer.html',{'error':error})
            if not customer.confirmIfUserPinIsCorrect(pin) :
                error = 'incorrect pin entered'
                return render(request,'transfer.html',{'error':error})
            try :
                receiver_customer = Customer.objects.get(account_number=account_number)
            except Customer.DoesNotExist:
                error = 'receiver account number is invalid'
                return render(request,'transfer.html',{'error':error})
            if transaction := Transaction.objects.create(sender=customer,receiver=receiver_customer,amount=amount,transaction_type='transfer'):
                receiver_customer.balance += float(amount)
                receiver_customer.save()
                customer.balance -= float(amount)
                customer.save()
                return redirect(f'/success/?amount={amount}&type=transfer&id={transaction.id}') 
        
        # THIS IS FOR THE GET REQUEST OF THIS PAGE 
        account_number = request.GET.get('account_number')
        return render(request,'transfer.html',{'account_number':account_number})
        
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})
    
@login_required(login_url='/login/')
def transactionPage(request):
    user : User = request.user
    transactions = Transaction.objects.filter(sender__user=user) | Transaction.objects.filter(receiver__user=user)
    transactions = transactions.order_by('-date')
    if user.is_superuser :
        return redirect("/admin/")
    try :
        return render(request,'transaction.html',{'transactions':transactions})
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})

def transactionDetailPage(request, transaction_id):
    user : User = request.user
    if user.is_superuser :
        return redirect("/admin/")
    try :
        transaction = Transaction.objects.get(id=transaction_id)
        if transaction.sender.user != user and transaction.receiver.user != user :
            return render(request,'404.html', {'error': 'transaction not found'})
        return render(request,'transaction_detail.html',{'transaction':transaction})
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})


@login_required(login_url='/login/')
def updateDetailPage(request):
    user : User = request.user
    if user.is_superuser :
        return redirect("/admin/")
    try :
        return render(request,'update_detail.html',{})
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})
    
@login_required(login_url='/login/')
def successPage(request):
    user : User = request.user
    if user.is_superuser :
        return redirect("/admin/")
    amount = request.GET.get('amount')
    transaction_type = request.GET.get('type')
    transaction_id = request.GET.get('id')
    try :
        return render(request,'success.html',{'amount':amount,'transaction_type':transaction_type,'transaction_id':transaction_id})
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})

@login_required(login_url='/login/')
def searchPage(request):
    user : User = request.user
    if user.is_superuser :
        return redirect("/admin/")
    account_found = None
    try :
        if request.GET.get("account_number"):
            account_number = request.GET.get('account_number')
            if len(account_number) != 10 or not account_number.isdigit() :
                error = 'account number must be a 10 digit number'
                return render(request,'search.html',{'error':error,'account_found':account_found})
            try :
                customer = Customer.objects.get(account_number=account_number)
                same_user = customer.user == user
                return render(request,'search.html',{'customer':customer, 'account_found':True,'same_user':same_user})
            except Customer.DoesNotExist:
                error = 'account number is invalid'
                
                return render(request,'search.html',{'error':error,'account_found':False})
        return render(request,'search.html',{})
    except Exception as e :
        return render(request,'404.html', {'error': str(e)})


def loginPage(request):
    error = '' 
    success = None
    # if form data is sent we retrieve those info
    if request.method == 'POST' :
        # PROCESS IT IN HERE 
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        
        if not email or len(email) < 2 :
            error = 'email must be a valid address'
        # do validation b4 creating a user  
        if not password  :
            error += '\nenter a password'
       
        # process at this stage 
        if not error :
            try : 
                # use the authenticate to find if that user exist or has signed up
                user = authenticate(request,username=email,password=password)
                if user :
                    login(request,user)
                    # get the next that is where they wanted to visit b4 they were bounced back 
                    place_to_redirect = request.GET.get("next")
                    if place_to_redirect : 
                        return redirect(place_to_redirect)
                    return redirect('user-home-page')
                else :
                    error = 'user does not exist'
            except Exception as e :
                error = str(e)
    return render(request, 'login.html', {'success':success, 'error':error})

def registerPage(request):
    error = '' 
    success = None
    # if form data is sent we retrieve those info
    if request.method == 'POST' :
        # PROCESS IT IN HERE 
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('password2')
        
        if not email or len(email) < 2 :
            error = 'email must be a valid address'
        # do validation b4 creating a user  
        if len(password) < 8 :
            error += '\nPassword length must be 8 or more characters'
        if password != confirm_password :
            error += '\nBoth password must match!'
        # process at this stage 
        if not error :
            try : 
                user =User.objects.create_user(username=email, email=email,password=password)
                success = 'Successfully signed up'
                return redirect('user-login-page')
            except Exception as e :
                error = str(e)
    return render(request, 'register.html', {'error':error, "success":success})

@login_required(login_url='user-login-page')
def logoutPage(request):
    logout(request)
    return redirect("user-login-page")