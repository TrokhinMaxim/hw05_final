from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseRedirect

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm

User = get_user_model()


def paginator_view(request, post_list):
    paginator = Paginator(post_list, settings.PAGINATOR_PAGES)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PAGINATOR_PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, settings.PAGINATOR_PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    paginator = Paginator(posts, settings.PAGINATOR_PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    count = Post.objects.filter(author=user).count()
    following = user.is_authenticated and user.following.exists()
    context = {
        'author': user,
        'count': count,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    count = post.author.posts.count()
    form = CommentForm(request.POST or None)
    context = {
        'count': count,
        'post': post,
        'form': form,
        'comments': post.comments.all()
    }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST, files=request.FILES or None)
        if not form.is_valid():
            return render(request, 'posts/create_post.html', {'form': form})
        form.instance.author = request.user
        form.save()
        return redirect('posts:profile', username=request.user)

    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        instance=post,
        files=request.FILES or None,
    )
    is_edit = True
    if post.author != request.user:
        return redirect('posts:index')
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
            'post': post,
            'is_edit': is_edit
        })
    form.save()
    return redirect('posts:post_detail', post_id=post.id)


@login_required
def follow_index(request):
    posts_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts_list, settings.PAGINATOR_PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    user = request.user
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
        return redirect(
            'posts:profile',
            username=username
        )
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.get(user=user, author__username=username).delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
