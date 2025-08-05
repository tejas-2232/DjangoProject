from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from urllib.parse import unquote
import json
from .models import UserDetails

# Create your views here.

def hello_world(request):
    #A view that returns Hello, world!
    
    return HttpResponse("Hello, world!")

@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        is_api = request.content_type == 'application/json'
        
        if is_api:
            # API request - parse JSON data
            try:
                data = json.loads(request.body)
                username = data.get('username')
                email = data.get('email')
                password = data.get('password')
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)
        else:
            username = request.POST.get('username')
            email = request.POST.get('email')
            password = request.POST.get('password')
        
        if not username or not email or not password:
            error_msg = 'All fields are required.'
            if is_api:
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'Loginify/signup.html')
        
        # Check if email already exists (unique constraint)
        if UserDetails.objects.filter(email=email).exists():
            error_msg = 'Email already exists. Please use a different email.'
            if is_api:
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'Loginify/signup.html')
        
        # Check if username already exists (primary key)
        if UserDetails.objects.filter(username=username).exists():
            error_msg = 'Username already exists. Please choose a different username.'
            if is_api:
                return JsonResponse({'status': 'error', 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return render(request, 'Loginify/signup.html')
        
        try:
            # Create new user
            user = UserDetails.objects.create(
                username=username,
                email=email,
                password=password
            )
            
            if is_api:
                return JsonResponse({
                    'status': 'success',
                    'message': 'User created successfully',
                    'user': {
                        'username': user.username,
                        'email': user.email,
                        'password': user.password
                    }
                }, status=201)
            else:
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')  # Redirect to login page upon successful signup
                
        except Exception as e:
            error_msg = 'An error occurred during signup. Please try again.'
            if is_api:
                return JsonResponse({'status': 'error', 'message': error_msg}, status=500)
            messages.error(request, error_msg)
            return render(request, 'Loginify/signup.html')
    
    # GET request - return signup form (web) or API info
    if request.content_type == 'application/json' or request.GET.get('format') == 'json':
        return JsonResponse({
            'message': 'Send POST request with JSON data: {"username": "...", "email": "...", "password": "..."}'
        })
    
    return render(request, 'Loginify/signup.html')

def login_view(request):
    #Login view - requires inputs for email and password.

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Both email and password are required.')
            return render(request, 'Loginify/login.html')
        
        try:
            # Check if user exists with provided email and password
            user = UserDetails.objects.get(email=email, password=password)

            # Successful login - display success message
            messages.success(request, f'Welcome back, {user.username}! Login successful.')
            return render(request, 'Loginify/success.html', {'user': user})
        
        except UserDetails.DoesNotExist:
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'Loginify/login.html')
    
    return render(request, 'Loginify/login.html')

#TASK 5: CRUD OPs

def get_all_users_view(request):
    """
    CRUD - READ: Get all user details - API endpoint
    """
    try:
        all_users = UserDetails.objects.all()
        users_data = [
            {
                'username': user.username,
                'email': user.email,
                'password': user.password
            }
            for user in all_users
        ]
        return JsonResponse({
            'status': 'success',
            'count': len(users_data),
            'users': users_data
        })
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to retrieve users'
        }, status=500)

def get_user_by_email_view(request, email):
    #Get single user by email
    try:
        # Decode URL-encoded email (handles %40 -> @, etc.)
        decoded_email = unquote(email)
        user = get_object_or_404(UserDetails, email=decoded_email)
        user_data = {
            'username': user.username,
            'email': user.email,
            'password': user.password
        }
        return JsonResponse({
            'status': 'success',
            'user': user_data
        })
    
    except Exception as e:
        decoded_email = unquote(email)
        return JsonResponse({
            'status': 'error',
            'message': f'User with email {decoded_email} not found'
        }, status=404)

#Update user details
@csrf_exempt
@require_http_methods(["GET", "POST", "PUT"])
def update_user_view(request, email):
    try:
        # Decode URL-encoded email (handles %40 -> @, etc.)
        decoded_email = unquote(email)
        user = get_object_or_404(UserDetails, email=decoded_email)
        
        if request.method == 'GET':
            # Return current user data
            return JsonResponse({
                'status': 'success',
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'password': user.password
                },
                'message': 'Use POST/PUT to update this user'
            })
        
        elif request.method in ['POST', 'PUT']:
            # Handle update - parse JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid JSON data'
                }, status=400)
            
            # Update user fields
            new_username = data.get('username', user.username)
            new_password = data.get('password', user.password)
            
            # Validate username uniqueness (if changed)
            if new_username != user.username and UserDetails.objects.filter(username=new_username).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username already exists'
                }, status=400)
            
            # Handle username change (primary key change requires special handling)
            if new_username != user.username:
                # Delete old record and create new one with same email
                old_email = user.email
                user.delete()
                user = UserDetails.objects.create(
                    username=new_username,
                    email=old_email,
                    password=new_password
                )
            else:
                # Just update password (no primary key change)
                user.password = new_password
                user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'User updated successfully',
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'password': user.password
                }
            })
    
    except UserDetails.DoesNotExist:
        decoded_email = unquote(email)
        return JsonResponse({
            'status': 'error',
            'message': f'User with email {decoded_email} not found'
        }, status=404)
    except Exception as e:
        decoded_email = unquote(email)
        return JsonResponse({
            'status': 'error',
            'message': f'Error updating user {decoded_email}: {str(e)}',
            'debug': str(type(e).__name__)
        }, status=500)

# Delete user by email
@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def delete_user_view(request, email):
    try:
        # Decode URL-encoded email (handles if %40 -> @, etc.)
        decoded_email = unquote(email)
        user = get_object_or_404(UserDetails, email=decoded_email)
        username = user.username  # Store for response message
        
        # Delete the user
        user.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': f'User {username} with email {decoded_email} deleted successfully'
        })
    
    except Exception as e:
        decoded_email = unquote(email)
        return JsonResponse({
            'status': 'error',
            'message': f'User with email {decoded_email} not found'
        }, status=404)