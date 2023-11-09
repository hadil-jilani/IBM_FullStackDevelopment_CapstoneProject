from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel
# from .restapis import related methods
from .restapis import analyze_review_sentiments, get_dealer_reviews_from_cf, get_dealers_from_cf, get_dealer_by_id, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.

# Create an `about` view to render a static about page
def about(request):
    return render(request, 'djangoapp/about.html')

# Create a `contact` view to return a static contact page
def contact(request):
    return render(request,'djangoapp/contact.html')
# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            print("Log in the user `{}`".format(username))
            login(request,user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request,'djangoapp/index.html',context)
    else:
        return render(request,'djangoapp/index.html',context)


# Create a `logout_request` view to handle sign out request
def logout_request(request):
    print("Log out the user `{}`".format(request.user.username))
    logout(request)
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context={}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html')
    elif request.method == 'POST':
        username = request.POST['username']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        password = request.POST['password']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.debug("{} is a new user".format(username))
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "User already exists."
            return render(request, 'djangoapp/register.html', context)


# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    context = {}
    if request.method == "GET":
        id = request.GET.get('dealerId')
        # id = request.params
        url = "http://localhost:3000/dealerships/get"
        if (id):
            dealerId = int(id)
            # Get specific dealership details by id
            dealerships = get_dealer_by_id(url, dealerId=dealerId) 
        else:
            # Get dealers from the URL
            dealerships = get_dealers_from_cf(url)
        context["dealership_list"] = dealerships
        # Concat all dealer's short name
        dealer_names = ' '.join([dealer.short_name for dealer in dealerships])
        print (context)
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)

# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == 'GET':
        context = {}
        url = "http://127.0.0.1:5000/api/get_reviews"
        # Get dealer data by id
        reviews = get_dealer_reviews_from_cf(url, dealerId=dealer_id)
        context["review_list"] = reviews
        reviews_list = " ".join([review.name + ": " + review.review +" Sentiment: " + str(review.sentiment) for review in reviews])
        return render(request, 'djangoapp/dealer_details.html', context)


# Create a `add_review` view to submit a review
def add_review(request, dealer_id):
    context = {}
    dealer_url = "http://localhost:3000/dealerships/get"
    dealer = get_dealer_by_id(dealer_url, dealerId=dealer_id)
    context["dealer"] = dealer
    if request.method == 'GET':
        # return HttpResponseRedirect(reversed(viewname='djangoapp:add_review'))
        # print('TEST')
        cars = CarModel.objects.all()
        context["cars"] = cars
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == 'POST':
        user = request.user
        if (user.is_authenticated):
            username = user.username
            car_id = request.POST['car']
            car = CarModel.objects.get(pk=car_id)
            review = {}
            review["time"] = datetime.utcnow().isoformat()
            review["name"] = username
            review["dealership"] = dealer_id
            review["car_make"] = car.car_make
            review["car_model"] = car.name
            review["car_year"] = int(car.year.strftime("%Y"))
            review["purchase_date"] = request.POST['purchase_date']
            review["review"] = request.POST['content']
            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    review["purchase"] = True
            json_payload = {"review": review}
            print("JSON Payload", json_payload)
            result = post_request(url='http://127.0.0.1:5000/api/post_review', **json_payload)
            print("Result: ",result)
            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)

