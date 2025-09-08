from django.shortcuts import render
from .models import MyBlog, BlogCategory, BlogTags, BlogComment
from django.shortcuts import get_object_or_404, redirect
from .forms import CommentForm, ReplyForm
from django.contrib import messages
# Create your views here.

def blog_home(request):
    blogs = MyBlog.objects.all()
    categories = BlogCategory.objects.all()
    tags = BlogTags.objects.all()
    context = {'blogs':blogs, 'categories':categories, 'tags':tags}
    return render(request, 'blog/blog_list.html', context)

def blog_details(request, slug):
    blog = get_object_or_404(MyBlog, slug=slug)
    categories = BlogCategory.objects.all()
    tags = BlogTags.objects.all()
    
    # Get all top-level comments (no parent) and prefetch replies
    comments = blog.comments.filter(parent__isnull=True).prefetch_related('replies')
    
    context = {
        'blog': blog,
        'categories': categories,
        'tags': tags,
        'comment_form': CommentForm(user=request.user),
        'reply_form': ReplyForm(user=request.user),
        'comments': comments,
    }
    return render(request, 'blog/blog_details.html', context)

def add_comment(request, slug):
    blog = get_object_or_404(MyBlog, slug=slug)

    if request.method == 'POST':
        form = CommentForm(request.POST, user=request.user)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            if request.user.is_authenticated:
                comment.user = request.user
            comment.save()
            messages.success(request, 'Your comment has been posted!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")

    return redirect('blog:blog-details', slug=blog.slug)

def add_reply(request, slug, comment_id):
    blog = get_object_or_404(MyBlog, slug=slug)
    parent_comment = get_object_or_404(BlogComment, id=comment_id)

    if request.method == 'POST':
        form = ReplyForm(request.POST, user=request.user)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.blog = blog
            reply.parent = parent_comment
            if request.user.is_authenticated:
                reply.user = request.user
            reply.save()
            messages.success(request, 'Your reply has been posted!')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")

    return redirect('blog:blog-details', slug=blog.slug)