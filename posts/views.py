from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()[:12]
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {"group": group,
               "posts": post_list,
               'page': page,
               'paginator': paginator, }
    return render(
        request,
        'group.html',
        context
    )


@login_required
def new_post(request):
    if request.method != 'POST':
        form = PostForm()
        return render(request, 'new.html', {'form': form})
    form = PostForm(request.POST, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    posts_count = author.author_posts.all().count()
    posts = author.author_posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follow_list = Follow.objects.filter(user_id=user.pk)
    ids = []
    for x in follow_list:
        ids.append(x.author_id)
    if author.pk in ids:
        following = True
    else:
        following = False
    context = {'following': following,
               'author': author,
               'posts_count': posts_count,
               'page': page,
               'paginator': paginator}
    return render(request,
                  'profile.html',
                  context)


def post_view(request, username, post_id):
    form = CommentForm()
    post = get_object_or_404(Post, id=post_id)
    author = post.author
    posts_count = author.author_posts.all().count()
    # Здесь переменные для комментов
    comments = Comment.objects.filter(post_id=post_id)
    context = {'author': author,
               'post': post,
               'form': form,
               'comments': comments,
               'posts_count': posts_count}
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    # Если юзер не автор то отправляем его на страницу поста
    if request.user.username != username:
        return redirect('post',
                        username=username,
                        post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if request.method == 'POST':
        if form.is_valid():  # Проверяем форму
            form.save()
            return redirect("post", username=request.user.username,
                            post_id=post_id)
    context = {'is_edit': True,
               'post': post,
               'form': form}
    return render(request, 'new.html', context)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # не выводит её в шаблон пользователской страницы 404
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, post_id, username):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post_id = post_id
        comment.author_id = request.user.id
        form.save()
    return redirect("post", username=username,
                    post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    follow_list = user.follower.all()
    following_posts = Post.objects.filter(author__following__user=request.user)
    post_list = following_posts
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {'page': page,
               'paginator': paginator}
    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        follow, created = Follow.objects.get_or_create(
            user=request.user, author=author)
        return redirect("follow_index")
    else:
        return redirect("index")


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    x = Follow.objects.get(user_id=user.pk, author_id=author.pk)
    x.delete()
    return redirect("follow_index")
