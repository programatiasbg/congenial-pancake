from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
from pytube import YouTube
import os
import assemblyai as aai
from openai import OpenAI
from .models import BlogPost


# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            youtube_link = data['link']
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)


        # get yt title - OK
        title = youtube_title(youtube_link)

        # get transcript - OK
        transcription = get_transcription(youtube_link)

        if not transcription:
            return JsonResponse({'error': " Failed to get transcript"}, status=500)


        # use OpenAI to generate the blog -ERRRO
        blog_content = generate_blog_from_transcription(transcription)
        print(f'##Blog content =>{blog_content}')

        if not blog_content:
            return JsonResponse({'error': " Failed to generate blog article"}, status=500)

        # save blog article to database
        new_blog_post = BlogPost.objects.create(
            user=request.user,
            youtube_title=title,
            youtube_link=youtube_link,
            generated_content=blog_content,
        )
        new_blog_post.save()
        # return blog article as a response
        return JsonResponse({'content': blog_content})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def youtube_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = os.environ.get('API_KEY_ASSEMBLYAI')
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text


def generate_blog_from_transcription(transicription):
    client = OpenAI(api_key = os.environ.get("OPENAI_API_KEY"))
    #os.environ.get("OPENAI_API_KEY")

    prompt = f"Based on the following transcription from a Youtube video, write a comprehensive blog post, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog post:\n\n{transicription}\n\n"

    message = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role":"user",
    "content":prompt}]

    # run the prompt
    llm_args = {"temperature": 0,
    "max_tokens": 100,
    "stream": False,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0}

    completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=message,
    **llm_args)

    print(f'**RESPONSE JSON DE TRANSCRIPTION=> {completion.choices[0].message.content.strip()}')

    return completion.choices[0].message.content.strip()


def blog_list(request):
    blog_posts = BlogPost.objects.filter(user=request.user)
    return render(request, 'blog-post-list.html', {'blog_posts': blog_posts})


def blog_details(request, pk):
    blog_post_details = BlogPost.objects.get(id=pk)
    if request.user == blog_post_details.user:
        return render(request, 'blog-post-details.html', {'blog_post_details': blog_post_details})
    else:
        return redirect('/')



def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')


def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message':error_message})

    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')
