from django.shortcuts import HttpResponse, redirect, render

def index(request):
	return render(request, 'login/index.html')

def attempt_login(request):
	try:
		print(request.META['HTTP_REFERER'])
	except KeyError:
		return redirect('index')

	return HttpResponse('BACON')