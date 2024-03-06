from django.shortcuts import render, redirect
from django.db.models import Q
from .models import Room, Topic, Message
from .forms import RoomForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm

def loginPage(request):
    # Set the variable 'page' to 'login'
    page = 'login'
    
    # Redirect to the home page if the user is already authenticated
    if request.user.is_authenticated:
        return redirect('home')
    
    # Process login form submission
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, "User does not exist.")
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Username or password does not exist.")

    # Render the login page with context
    context = {'page': page}
    return render(request, 'base/login_register.html', context)



def logoutUser(request):
    # Logout the user and redirect to the home page
    logout(request)
    return redirect('home')


def registerUser(request):
    # Create an instance of UserCreationForm
    form = UserCreationForm()
    
    # Process user registration form submission
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')
    
    # Render the registration page with context
    return render(request, 'base/login_register.html', {'form': form})



def home(request):
    # Search bar - filter rooms and messages based on the query parameter 'q'
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )
    topics = Topic.objects.all()
    topics_count = topics.count()
    room_count = rooms.count()
    room_messages = Message.objects.all().order_by('-created').filter(Q(room__topic__name__icontains=q))
    
    # Context for rendering the home page
    context = {
        'rooms': rooms, 
        'topics': topics, 
        'room_count': room_count, 
        'room_messages': room_messages,
        'topics_count': topics_count,
    }
    return render(request, 'base/home.html', context)



def room(request, pk):
    # Get the room, its messages, and participants based on the room's ID
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()
    participants_count = participants.count()
    
    # Process message submission form
    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)
    
    # Context for rendering the room page
    context = {
        'room': room,
        'room_messages': room_messages, 
        'participants': participants,
        'participants_count': participants_count,
    }
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    # Get user information, rooms, messages, and topics based on the user's ID
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    
    # Context for rendering the user profile page
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages}
    return render(request, 'base/profile.html', context)



@login_required(login_url='login')
def createRoom(request):
    # Create an instance of RoomForm
    form = RoomForm()
    
    # Process room creation form submission
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save(commit=False)
            room.host = request.user
            room.save()
            return redirect('home')
    
    # Context for rendering the room creation form page
    context = {'form': form}
    return render(request, 'base/room_form.html', context)



@login_required(login_url='login')
def updateRoom(request, pk):
    # Get the room and create an instance of RoomForm with the room data
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    
    # Check if the user is the host of the room
    if request.user != room.host:
        return HttpResponse('You are not allowed here')
    
    # Process room update form submission
    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')
    
    # Context for rendering the room update form page
    context ={'form': form}
    return render(request, 'base/room_form.html', context)



@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    
    if request.method == 'POST':
        room.delete()
        return redirect('home')
    
    return render(request, 'base/delete.html', {'obj':room}) 


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    
    if request.user != message.user:
        return HttpResponse('You are not allowed here')
    
    if request.method == 'POST':
        message.delete()
        return redirect('home')
    
    return render(request, 'base/delete.html', {'obj': message}) 


