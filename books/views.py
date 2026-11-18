from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST

from core.models import (
    Copy, Exchange, ExchangeStatusLog,
    Genre, ReaderProfile, Review,
)
from .forms import BookForm, RegisterForm
from .models import Favorite, Notification

User = get_user_model()


def home(request):
    latest = (
        Copy.objects.filter(
            is_available=True,
            moderation_status=Copy.ModerationStatus.APPROVED,
        )
        .select_related('book', 'owner__reader')
        .prefetch_related('photos', 'book__genres')[:6]
    )
    return render(request, 'books/home.html', {'latest': latest})


def catalog(request):
    qs = (
        Copy.objects.filter(
            is_available=True,
            moderation_status=Copy.ModerationStatus.APPROVED,
        )
        .select_related('book', 'owner__reader')
        .prefetch_related('photos', 'book__genres')
    )
    q = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    genre = request.GET.get('genre', '').strip()
    condition = request.GET.get('condition', '').strip()
    if q:
        qs = qs.filter(
            Q(book__title__icontains=q)
            | Q(book__author__icontains=q)
            | Q(book__bookgenre__genre__name__icontains=q)
        ).distinct()
    if city:
        qs = qs.filter(city__icontains=city)
    if genre:
        qs = qs.filter(book__bookgenre__genre__name=genre)
    if condition:
        qs = qs.filter(condition=condition)
    qs = qs.order_by('book__title') if request.GET.get('sort') == 'title' else qs.order_by('-created_at')

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_params = request.GET.copy()
    query_params.pop('page', None)

    return render(request, 'books/catalog.html', {
        'books': page_obj.object_list,
        'page_obj': page_obj,
        'query_params': query_params.urlencode(),
        'genres': Genre.objects.all(),
        'q': q,
        'city': city,
        'selected_genre': genre,
        'condition': condition,
    })


def book_detail(request, pk):
    copy = get_object_or_404(
        Copy.objects.select_related('book', 'owner__reader')
        .prefetch_related('photos', 'book__genres'),
        pk=pk,
    )
    is_favorite = request.user.is_authenticated and Favorite.objects.filter(user=request.user, copy=copy).exists()
    return render(request, 'books/book_detail.html', {'book': copy, 'is_favorite': is_favorite})


def register(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Аккаунт создан. Добро пожаловать!')
        return redirect('profile')
    return render(request, 'registration/register.html', {'form': form})


@login_required
def add_book(request):
    form = BookForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        copy = form.save(request.user.readerprofile)
        messages.success(request, 'Книга отправлена на модерацию.')
        Notification.objects.create(
            user=request.user,
            title='Книга отправлена на модерацию',
            body=f'Экземпляр «{copy.book.title}» ожидает проверки.',
            url='/profile/',
        )
        return redirect('profile')
    return render(request, 'books/book_form.html', {'form': form, 'title': 'Добавить книгу'})


@login_required
def profile(request, username=None):
    target = get_object_or_404(User, email=username) if username else request.user
    profile_obj = get_object_or_404(ReaderProfile, reader=target)
    books = profile_obj.copies.filter(moderation_status=Copy.ModerationStatus.APPROVED).select_related('book').prefetch_related('photos')
    stats = profile_obj.copies.aggregate(total=Count('id'))
    reviews = Review.objects.filter(target=profile_obj).select_related('author__reader')
    return render(request, 'books/profile.html', {
        'target': target,
        'target_profile': profile_obj,
        'books': books,
        'stats': stats,
        'reviews': reviews,
    })


@login_required
def edit_profile(request):
    profile_obj, _ = ReaderProfile.objects.get_or_create(
        reader=request.user,
        defaults={'display_name': request.user.email.split('@')[0], 'city': 'Не указан'},
    )
    if request.method == 'POST':
        request.user.email = request.POST.get('email', '').strip()[:254]
        request.user.save(update_fields=['email'])
        profile_obj.display_name = request.POST.get('display_name', '').strip()[:60]
        profile_obj.city = request.POST.get('city', '').strip()[:80]
        profile_obj.save(update_fields=['display_name', 'city'])
        messages.success(request, 'Профиль обновлён.')
        return redirect('profile')
    return render(request, 'books/edit_profile.html', {'profile': profile_obj})


@login_required
def exchanges(request):
    qs = (
        Exchange.objects.filter(Q(requester__reader=request.user) | Q(copy__owner__reader=request.user))
        .select_related('copy__book', 'requester__reader', 'copy__owner__reader')
        .order_by('-created_at')
    )
    return render(request, 'books/exchanges.html', {'exchanges': qs})


@login_required
@require_POST
def propose_exchange(request, pk):
    copy = get_object_or_404(
        Copy,
        pk=pk,
        is_available=True,
        moderation_status=Copy.ModerationStatus.APPROVED,
    )
    if copy.owner.reader_id == request.user.id:
        messages.error(request, 'Нельзя предложить обмен на собственную книгу.')
        return redirect('book_detail', pk=pk)
    if Exchange.objects.filter(
        copy=copy,
        requester=request.user.readerprofile,
        status__in=[Exchange.Status.NEW, Exchange.Status.ACCEPTED],
    ).exists():
        messages.info(request, 'У вас уже есть активный запрос.')
        return redirect('exchanges')

    with transaction.atomic():
        exchange = Exchange.objects.create(
            copy=copy,
            requester=request.user.readerprofile,
            status=Exchange.Status.NEW,
            method='',
        )
        ExchangeStatusLog.objects.create(
            exchange=exchange,
            old_status=Exchange.Status.NEW,
            new_status=Exchange.Status.NEW,
            changed_by=request.user,
        )
        Notification.objects.create(
            user=copy.owner.reader,
            title='Новое предложение обмена',
            body=f'{request.user.username} предлагает обмен на «{copy.book.title}».',
            url='/exchanges/',
        )
    messages.success(request, 'Предложение отправлено владельцу.')
    return redirect('exchanges')


@login_required
@require_POST
def exchange_action(request, pk, action):
    exchange = get_object_or_404(
        Exchange.objects.select_related('copy__owner__reader', 'requester__reader', 'copy__book'),
        pk=pk,
    )
    old_status = exchange.status
    owner = exchange.copy.owner.reader
    requester = exchange.requester.reader

    if action in ('accept', 'decline') and owner != request.user:
        messages.error(request, 'Только владелец может изменить входящий запрос.')
        return redirect('exchanges')
    if action == 'cancel' and requester != request.user:
        messages.error(request, 'Отменить запрос может только его автор.')
        return redirect('exchanges')

    if action == 'accept' and exchange.status == Exchange.Status.NEW:
        exchange.status = Exchange.Status.ACCEPTED
        exchange.copy.is_available = False
        exchange.copy.save(update_fields=['is_available'])
    elif action == 'decline' and exchange.status == Exchange.Status.NEW:
        exchange.status = Exchange.Status.CANCELLED
    elif action == 'cancel' and exchange.status in (Exchange.Status.NEW, Exchange.Status.ACCEPTED):
        exchange.status = Exchange.Status.CANCELLED
        if not exchange.copy.exchanges.filter(status=Exchange.Status.ACCEPTED).exclude(pk=exchange.pk).exists():
            exchange.copy.is_available = True
            exchange.copy.save(update_fields=['is_available'])
    elif action == 'complete' and exchange.status == Exchange.Status.ACCEPTED and owner == request.user:
        exchange.status = Exchange.Status.DONE
    else:
        messages.error(request, 'Действие недоступно для текущего статуса.')
        return redirect('exchanges')

    with transaction.atomic():
        exchange.save(update_fields=['status', 'updated_at'])
        ExchangeStatusLog.objects.create(
            exchange=exchange,
            old_status=old_status,
            new_status=exchange.status,
            changed_by=request.user,
        )
        Notification.objects.create(
            user=requester if request.user == owner else owner,
            title='Обновлён статус обмена',
            body=f'Обмен №{exchange.pk}: {exchange.get_status_display()}.',
            url='/exchanges/',
        )
    messages.success(request, 'Статус обмена обновлён.')
    return redirect('exchanges')


@login_required
@require_POST
def toggle_favorite(request, pk):
    copy = get_object_or_404(Copy, pk=pk)
    favorite, created = Favorite.objects.get_or_create(user=request.user, copy=copy)
    if not created:
        favorite.delete()
    return redirect('book_detail', pk=pk)


def staff_check(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(staff_check)
def moderation(request):
    copies = (
        Copy.objects.filter(moderation_status=Copy.ModerationStatus.PENDING)
        .select_related('book', 'owner__reader')
        .prefetch_related('photos')
    )
    return render(request, 'books/moderation.html', {'books': copies})


@user_passes_test(staff_check)
@require_POST
def moderate_book(request, pk, action):
    copy = get_object_or_404(Copy.objects.select_related('book', 'owner__reader'), pk=pk)
    if action == 'approve':
        copy.moderation_status = Copy.ModerationStatus.APPROVED
        copy.is_available = True
    elif action == 'reject':
        copy.moderation_status = Copy.ModerationStatus.REJECTED
        copy.is_available = False
    else:
        messages.error(request, 'Неизвестное действие.')
        return redirect('moderation')
    copy.save(update_fields=['moderation_status', 'is_available'])
    Notification.objects.create(
        user=copy.owner.reader,
        title='Результат модерации',
        body=f'Книга «{copy.book.title}»: {copy.get_moderation_status_display()}.',
        url='/profile/',
    )
    messages.success(request, 'Результат модерации сохранён.')
    return redirect('moderation')
