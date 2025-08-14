from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from urllib.parse import unquote
import json
import os
from functools import wraps
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import UserDetails

# File validation utility
def validate_image_file(file):
    """
    Validate uploaded image file
    """
    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        return False, "File size too large. Maximum size is 5MB."
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in allowed_extensions:
        return False, f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check if file is actually an image
    try:
        from PIL import Image
        image = Image.open(file)
        image.verify()
        return True, "Valid image file"
    except Exception as e:
        return False, "Invalid image file or corrupted file."

# Session utility decorator
def login_required_session(view_func):
    """
    Decorator that requires an active session for access
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            messages.error(request, 'Please log in to access this page.')
            return redirect('login')
        
        # Verify session user still exists
        try:
            UserDetails.objects.get(username=request.session['user_id'])
        except UserDetails.DoesNotExist:
            # Session user no longer exists, clear session
            request.session.flush()
            messages.error(request, 'Account no longer exists. Please log in again.')
            return redirect('login')
            
        return view_func(request, *args, **kwargs)
    return wrapper

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
                # Auto-login after successful signup (create session)
                request.session['user_id'] = user.username
                request.session['user_email'] = user.email
                request.session['is_logged_in'] = True
                request.session.set_expiry(86400)  # 24 hours
                
                messages.success(request, f'Account created successfully! Welcome, {user.username}!')
                return render(request, 'Loginify/success.html', {'user': user})
                
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
    # Check if user is already logged in
    if request.session.get('user_id'):
        # User is already logged in, redirect to dashboard/success page
        user = UserDetails.objects.get(username=request.session['user_id'])
        messages.info(request, f'You are already logged in as {user.username}.')
        return render(request, 'Loginify/success.html', {'user': user})

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Both email and password are required.')
            return render(request, 'Loginify/login.html')
        
        try:
            # Check if user exists with provided email and password
            user = UserDetails.objects.get(email=email, password=password)

            # Successful login - create session
            request.session['user_id'] = user.username
            request.session['user_email'] = user.email
            request.session['is_logged_in'] = True
            
            # Set session expiry (optional - 24 hours)
            request.session.set_expiry(86400)  # 24 hours in seconds
            
            messages.success(request, f'Welcome back, {user.username}! Login successful.')
            return render(request, 'Loginify/success.html', {'user': user})
        
        except UserDetails.DoesNotExist:
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'Loginify/login.html')
    
    return render(request, 'Loginify/login.html')

def logout_view(request):
    """
    Logout view - clears session data and logs out the user
    """
    if request.session.get('user_id'):
        username = request.session.get('user_id')
        # Clear all session data
        request.session.flush()  # This clears all session data and deletes the session cookie
        messages.success(request, f'You have been successfully logged out, {username}!')
    else:
        messages.info(request, 'You were not logged in.')
    
    return redirect('login')

@login_required_session
def dashboard_view(request):
    """
    Dashboard view - only accessible to logged-in users
    """
    # Get user from session (decorator ensures user exists)
    user = UserDetails.objects.get(username=request.session['user_id'])
    return render(request, 'Loginify/dashboard.html', {'user': user})

@login_required_session
def profile_view(request):
    """
    Profile view - shows user profile for logged-in users
    """
    # Get user from session (decorator ensures user exists)
    user = UserDetails.objects.get(username=request.session['user_id'])
    
    # Check for session data consistency
    if user.email != request.session.get('user_email'):
        # Session data is inconsistent, refresh it
        request.session['user_email'] = user.email
    
    context = {
        'user': user,
        'session_info': {
            'session_key': request.session.session_key,
            'expiry_date': request.session.get_expiry_date(),
            'logged_in_since': request.session.get('user_id')
        }
    }
    return render(request, 'Loginify/profile.html', context)

def session_info_view(request):
    """
    Session information view - shows current session details for testing
    """
    session_data = {
        'session_key': request.session.session_key,
        'is_logged_in': request.session.get('is_logged_in', False),
        'user_id': request.session.get('user_id'),
        'user_email': request.session.get('user_email'),
        'session_exists': bool(request.session.session_key),
        'expiry_date': request.session.get_expiry_date() if request.session.session_key else None,
        'all_session_keys': list(request.session.keys())
    }
    
    return JsonResponse({
        'status': 'success',
        'session_info': session_data,
        'message': 'Session information retrieved successfully'
    })

@login_required_session
@csrf_exempt
def upload_profile_picture(request):
    """
    Handle profile picture upload and update
    """
    if request.method == 'POST':
        # Get current user
        user = UserDetails.objects.get(username=request.session['user_id'])
        
        # Check if file was uploaded
        if 'profile_picture' not in request.FILES:
            messages.error(request, 'No file selected for upload.')
            return redirect('profile')
        
        uploaded_file = request.FILES['profile_picture']
        
        # Validate the uploaded file
        is_valid, error_message = validate_image_file(uploaded_file)
        if not is_valid:
            messages.error(request, error_message)
            return redirect('profile')
        
        try:
            # Delete old profile picture if exists
            if user.profile_picture:
                user.delete_old_profile_picture()
            
            # Save new profile picture
            user.profile_picture = uploaded_file
            user.save()
            
            messages.success(request, 'Profile picture updated successfully!')
            
            # Return JSON response for AJAX requests
            if request.content_type == 'application/json' or request.GET.get('format') == 'json':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Profile picture updated successfully',
                    'profile_picture_url': user.get_profile_picture_url()
                })
            
        except Exception as e:
            error_msg = 'An error occurred while uploading the profile picture.'
            messages.error(request, error_msg)
            
            if request.content_type == 'application/json' or request.GET.get('format') == 'json':
                return JsonResponse({
                    'status': 'error',
                    'message': error_msg
                }, status=500)
    
    return redirect('profile')

@login_required_session
def remove_profile_picture(request):
    """
    Remove user's profile picture
    """
    if request.method == 'POST':
        user = UserDetails.objects.get(username=request.session['user_id'])
        
        try:
            if user.profile_picture:
                # Delete the file
                user.delete_old_profile_picture()
                # Clear the field
                user.profile_picture = None
                user.save()
                messages.success(request, 'Profile picture removed successfully!')
            else:
                messages.info(request, 'No profile picture to remove.')
                
        except Exception as e:
            messages.error(request, 'An error occurred while removing the profile picture.')
    
    return redirect('profile')

#TASK 5: CRUD OPs

def get_all_users_view(request):
    """
    CRUD - READ: Get all user details - API endpoint
    Note: This endpoint requires an active session for security
    """
    # Check if user is logged in via session (for web interface protection)
    if not request.session.get('user_id') and request.content_type != 'application/json':
        return JsonResponse({
            'status': 'error',
            'message': 'Session required for web access. Please login first.',
            'redirect': '/login/'
        }, status=401)
    
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
        
        response_data = {
            'status': 'success',
            'count': len(users_data),
            'users': users_data
        }
        
        # Add session info if user is logged in via web interface
        if request.session.get('user_id'):
            response_data['session_user'] = request.session.get('user_id')
            
        return JsonResponse(response_data)
    
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