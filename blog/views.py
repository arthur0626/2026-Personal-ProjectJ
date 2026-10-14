from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import BlogPostForm, CommentForm, UploadForm
from .models import Attachment, BlogPost, Comment


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


def detail(request, slug, comment_form=None):
    posts = BlogPost.objects.public()
    if request.user.is_authenticated:
        # The author may preview their own drafts and private posts.
        posts = posts | BlogPost.objects.filter(author=request.user)
    post = get_object_or_404(posts, slug=slug)
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': post.comments.all() if post.is_public else [],
        'comment_form': comment_form or CommentForm(user=request.user),
    }, status=400 if comment_form else 200)


@require_POST
def comment_create(request, slug):
    post = get_object_or_404(BlogPost.objects.public(), slug=slug)
    form = CommentForm(request.POST, user=request.user)
    if not form.is_valid():
        return detail(request, slug, comment_form=form)
    form.instance.post = post
    form.save()
    return redirect(f"{post.get_absolute_url()}#comments")


@require_POST
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk, post__in=BlogPost.objects.public())
    # shortcut: no rate limit on guest password attempts; add one in Milestone 10.
    if comment.can_delete(request.user, request.POST.get('password', '')):
        comment.delete()
    else:
        messages.error(request, '댓글을 삭제할 권한이 없거나 비밀번호가 틀렸습니다.')
    return redirect(f"{comment.post.get_absolute_url()}#comments")


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


@owner_required
@require_POST
def upload(request):
    form = UploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({'error': '파일이 없습니다.'}, status=400)
    try:
        attachment = Attachment.from_upload(form.cleaned_data['file'], request.user)
    except ValidationError as error:
        return JsonResponse({'error': error.messages[0]}, status=400)
    return JsonResponse({
        'url': attachment.file.url, 'name': attachment.name, 'is_image': attachment.is_image,
    })
