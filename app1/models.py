from django.db import models
from django.contrib.auth.models import User
from random import randint
from django.contrib.auth.hashers import make_password, check_password 


GENDER_CHOICES = (
    ('m',"Male"),
    ('f',"Female"),
    ('u',"Unspecified")
)


def generateAccountNumber():
    return f'74{randint(10000000,99999999)}'

   
Transaction_Type = (
    ('transfer', "Transfer"),
    ('deposit', "Deposit"),
    ('withdraw', "Withdraw"),
)

def generateVoucherCode()->str :
    voucher_code = f'VC{randint(1000000000,9999999999)}'
    return voucher_code

# Create your models here.
class Customer(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    gender = models.CharField(max_length=1,choices=GENDER_CHOICES,default='u')
    account_number = models.CharField(max_length=10,blank=False,unique=True,default=generateAccountNumber, editable=True)
    balance = models.FloatField(default=200.00)
    pin = models.CharField(max_length=128, null=True,blank=True,editable=False)
    
    
    def hashUserPin(self,raw_pin):
        self.pin = make_password(raw_pin)
        self.save()
        
    def confirmIfUserPinIsCorrect(self,raw_pin)->bool :
        return check_password(raw_pin,self.pin)
    
    def __str__(self):
        return f'{self.user.username} => NGN{self.balance}'
    

    
class Transaction(models.Model):
    sender = models.ForeignKey(to=Customer, on_delete=models.CASCADE, related_name='transaction_sender')
    receiver = models.ForeignKey(to=Customer, on_delete=models.CASCADE, related_name='transaction_reciever')
    amount = models.FloatField()
    transaction_type = models.CharField(max_length=10, choices=Transaction_Type)
    date = models.DateTimeField(auto_now_add=True)
    # description
    def __str__(self):
        return f"{self.transaction_type} => NGN{self.amount}"
        

class Voucher(models.Model):
    customer = models.ForeignKey(to=Customer,on_delete=models.CASCADE)
    code = models.CharField(max_length=12, default=generateVoucherCode, unique=True)
    amount = models.FloatField()
    is_loaded = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.customer.user.username} => voucher of NGN{self.amount} has {'been ' if self.is_loaded else "not "} loaded"
     
    
    
