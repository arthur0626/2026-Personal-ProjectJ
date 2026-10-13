from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BlogPostForm
from .models import BlogPost


def owner_required(view):
    """Registration is open, so only staff accounts may author posts."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return login_required(wrapper)


def index(request):
    return render(request, 'blog/index.html', {'posts': BlogPost.objects.public()})


def detail(request, slug):
    posts = BlogPost.objects.public()
    if request.user.is_authenticated:
        # The author may preview their own drafts and private posts.
        posts = posts | BlogPost.objects.filter(author=request.user)
    return render(request, 'blog/detail.html', {
        'post': get_object_or_404(posts, slug=slug),
    })


@owner_required
def drafts(request):
    return render(request, 'blog/drafts.html', {
        'posts': BlogPost.objects.filter(author=request.user),
    })


@owner_required
def edit(request, pk=None):
    if pk:
        post = get_object_or_404(BlogPost, pk=pk, author=request.user)
    else:
        post = BlogPost(author=request.user)
    form = BlogPostForm(request.POST or None, instance=post)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('blog:edit', pk=post.pk)
    return render(request, 'blog/edit.html', {'form': form, 'post': post})


@owner_required
@require_POST
def set_published(request, pk, published):
    post = get_object_or_404(BlogPost, pk=pk, author=request.user)
    if published:
        post.publish()
    else:
        post.unpublish()
    return redirect('blog:edit', pk=pk)
