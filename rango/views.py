from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime

# helper method to get cookies from the server
def get_server_side_cookie(request, cookie, default_val=None):
	val = request.session.get(cookie)
	if not val:
		val = default_val
	return val

# cookie handling helper method
def visitor_cookie_handler(request):
	# Get the number of visits
	visits = int(get_server_side_cookie(request, 'visits', '1'))
	last_visit_cookie = get_server_side_cookie(request, 'last_visit', str(datetime.now()))
	last_visit_time = datetime.strptime(last_visit_cookie[:-7], '%Y-%m-%d %H:%M:%S')
	
	# If it's been more than a day since the last visit, then:
	# increment visits counter and update time in last visit cookie
	if (datetime.now() - last_visit_time).days > 0:
		visits = visits + 1
		request.session['last_visit'] = str(datetime.now())
	
	else:
		# Set a new, up-to-date last visit cookie
		request.session['last_visit'] = last_visit_cookie

	# Update/set the visits cookie
	request.session['visits'] = visits


def index(request):
	# Query the database for a list of ALL categories currently stored.
	# Order the categories by the number of likes in descending order.
	# Retrieve the top 5 only (or all if less than 5).
	category_list = Category.objects.order_by('-likes')[:5]
	pages_list = Page.objects.order_by('-views')[:5]

	context_dict = {}
	context_dict['boldmessage'] = 'Crunchy, creamy, cookie, candy, cupcake!'
	context_dict['categories'] = category_list
	context_dict['pages'] = pages_list

	# Update visits cookie
	visitor_cookie_handler(request)

	# Render the response and return it
	return render(request, 'rango/index.html', context=context_dict)

def about(request):
	# Look for visits cookie in server
	visitor_cookie_handler(request)
	context_dict = {'visits' : request.session['visits']}

	return render(request, 'rango/about.html', context=context_dict)

def show_category(request, category_name_slug):
	context_dict = {}
	try:
		# Can we find a category name slug with the given name?
		# If we can't, the .get() method raises a DoesNotExist exception.
		category = Category.objects.get(slug=category_name_slug) 
		# Retrieve all of the associated pages.
		pages = Page.objects.filter(category=category) 
		
		context_dict['pages'] = pages # Adds our results list to the template context under name pages.
		context_dict['category'] = category

	except Category.DoesNotExist:
		# We get here if we didn't find the specified category.
		# Don't do anything -
		# the template will display the "no category" message for us.
		context_dict['category'] = None
		context_dict['pages'] = None

	# Go render the response and return it to the client.
	return render(request, 'rango/category.html', context=context_dict)

@login_required
def add_category(request):
	form = CategoryForm()

	if request.method == 'POST':
		form = CategoryForm(request.POST)

		if form.is_valid():
			#save the new category to the db.
			form.save(commit=True)
			return redirect('/rango/')

		else:
			print(form.errors)

	#renders the form with error messages (if any)
	return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):
	try:
		category = Category.objects.get(slug=category_name_slug)
	except Category.DoesNotExist:
		category = None

	if category is None:
		return redirect('/rango/')
	
	form = PageForm()
	
	if request.method == 'POST':
		form = PageForm(request.POST)
		
		if form.is_valid():
			if category:
				page = form.save(commit=False)
				page.category = category
				page.views = 0
				page.save()

				return redirect(reverse('rango:show_category', kwargs={'category_name_slug': category_name_slug}))
		
		else:
			print(form.errors)

	context_dict = {'form': form, 'category': category}
	return render(request, 'rango/add_page.html', context=context_dict)

# Register a new user
def register(request):
	registered = False # Boolean indicator tells if registration was successful - change to true when successfully registered

	if request.method == 'POST':
		user_form = UserForm(request.POST)
		profile_form = UserProfileForm(request.POST)

		# If the forms are valid, save form data to db.
		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save()

			user.set_password(user.password) # Has password with pre-built Django hashing method
			user.save()

			# Delay committing until ready, save UserProfile instance
			profile = profile_form.save(commit=False)
			profile.user = user

			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']

			profile.save()

			registered = True

		else:
			print(user_form.errors, profile_form.errors)

	else: # Mustn't be a HTTP POST so render our form using two blank forms
		user_form = UserForm()
		profile_form = UserProfileForm()

	return render(
				request,
				'rango/register.html',
				context = {	'user_form' : user_form,
							'profile_form' : profile_form,
							'registered' : registered}
				)

def user_login(request):
	# If request is a POST, login attempt has been made
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')

 		# Django inbuilt user/password validation
		# returns User object if it is valid
		user = authenticate(username=username, password=password)

		if user: # true if authentication passed
			if user.is_active: # i.e. is the user currently enabled?
				login(request, user)
				return redirect(reverse('rango:index'))

			else:
				return HttpResponse("Your Rango account is disabled.")
		
		else: # bad login details provided
			print(f"Invalid login details: {username}, {password}")
			return HttpResponse("Invalid login details supplied.")

	# Default to treat request as a HTTP GET
	else:
		return render(request,'rango/login.html')

@login_required
def user_logout(request):
	logout(request)
	return redirect(reverse('rango:index'))

@login_required
def restricted(request):
	return render(request, 'rango/restricted.html')