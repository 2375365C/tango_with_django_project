from django.shortcuts import render
from django.http import HttpResponse
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm
from django.shortcuts import redirect
from django.urls import reverse

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
	# Render the response and send it back!
	return render(request, 'rango/index.html', context=context_dict)

def about(request):
	return render(request, 'rango/about.html')

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