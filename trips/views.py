from datetime import datetime
from .models import Trip, TripParticipant, Category, Proposal, Vote, Message
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from .models import Trip, TripParticipant, Category, Proposal, Vote
from .forms import TripForm
from urllib.parse import urlencode

def home(request):
    return render(request, 'home.html')

def enter(request):
    return render(request, 'enter.html')

def join_trip_info(request):
    return render(request, 'join_trip_info.html')

@login_required
def my_trips(request):
    trips = (
        Trip.objects
        .filter(participants__user=request.user)
        .distinct()
        .order_by('-created_at')
    )
    pending_trip_id = request.session.pop('pending_join_trip_id', None)

    if pending_trip_id:
        pending_trip = get_object_or_404(Trip, pk=pending_trip_id)

        TripParticipant.objects.get_or_create(
            trip=pending_trip,
            user=request.user,
            defaults={'role': 'member'}
        )

        messages.success(request, f"You've joined {pending_trip.title}!")
        return redirect('trip_detail', pk=pending_trip.pk)
    created_trips = trips.filter(leader=request.user)
    participating_trips = trips.exclude(leader=request.user)

    trip_dates = {}

    for trip in trips:
        dates_category = trip.categories.filter(name='Dates').first()

        if dates_category:
            locked_dates = dates_category.proposals.filter(is_locked=True).order_by('created_at')
            trip_dates[trip.id] = locked_dates.first().title if locked_dates.exists() else None
        else:
            trip_dates[trip.id] = None

    return render(request, 'my_trips.html', {
        'trips': trips,
        'created_trips': created_trips,
        'participating_trips': participating_trips,
        'trip_dates': trip_dates,
    })

@login_required
def create_trip(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.leader = request.user
            trip.save()
            TripParticipant.objects.create(trip=trip, user=request.user, role='leader')
            for cat_name in ['Destination', 'Dates', 'Μετάβαση', 'Διαμονή']:
                Category.objects.get_or_create(trip=trip, name=cat_name, defaults={'max_proposals': 10})
            return redirect('trip_detail', pk=trip.pk)
    else:
        form = TripForm()
    return render(request, 'create_trip.html', {'form': form})

@login_required
def trip_detail(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    for cat_name in ['Destination', 'Dates', 'Μετάβαση', 'Διαμονή']:
        Category.objects.get_or_create(trip=trip, name=cat_name, defaults={'max_proposals': 10})
    def get_category_data(cat_name):
        cat = trip.categories.filter(name=cat_name).first()
        if not cat:
            return None
        proposals = cat.proposals.all()
        can_add = proposals.count() < cat.max_proposals
        proposals_data = []
        for p in proposals:
            avg = p.votes.aggregate(Avg('score'))['score__avg'] or 0
            proposals_data.append({
                'proposal': p,
                'avg_score': avg,
                'total_votes': p.votes.count(),
            })
        return {
            'category': cat,
            'proposals': proposals_data,
            'can_add': can_add,
        }
    destination_data = get_category_data('Destination')
    dates_data = get_category_data('Dates')
    transport_data = get_category_data('Μετάβαση')
    stay_data = get_category_data('Διαμονή')

    summary = {}
    for name, data in [('Destination', destination_data), ('Dates', dates_data), ('Μετάβαση', transport_data), ('Διαμονή', stay_data)]:
        agreed_list = []
        if data and data['proposals']:
            locked = [p for p in data['proposals'] if p['proposal'].is_locked]
            locked.sort(key=lambda x: x['proposal'].created_at)
            for p in locked:
                agreed_list.append(p['proposal'].title)
        summary[name] = agreed_list
    participant_count = trip.participants.count()
    is_leader = trip.leader == request.user  
    return render(request, 'trip_detail.html', {
        'trip': trip,
        'destination_data': destination_data,
        'dates_data': dates_data,
        'transport': transport_data,
        'stay': stay_data,
        'summary': summary,
        'participant_count': participant_count,
        'is_leader': is_leader,
    })

@login_required
def add_proposal(request, trip_pk, category_pk):
    trip = get_object_or_404(Trip, pk=trip_pk)
    category = get_object_or_404(Category, pk=category_pk, trip=trip)

    if not TripParticipant.objects.filter(trip=trip, user=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Not a member.'}, status=403)

    if request.method == 'POST':
        participant = TripParticipant.objects.get(trip=trip, user=request.user)

        if category.name == 'Dates':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            if not start_date or not end_date:
                return JsonResponse({'success': False, 'error': 'Both dates are required.'})

            from datetime import datetime

            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')

            if end_dt < start_dt:
                return JsonResponse({'success': False, 'error': 'End date cannot be before start date.'})

            if start_dt.year == end_dt.year and start_dt.month == end_dt.month:
                title = f"{start_dt.day}–{end_dt.day} {start_dt.strftime('%b')} {start_dt.year}"
            elif start_dt.year == end_dt.year:
                title = f"{start_dt.day} {start_dt.strftime('%b')} – {end_dt.day} {end_dt.strftime('%b')} {start_dt.year}"
            else:
                title = f"{start_dt.day} {start_dt.strftime('%b')} {start_dt.year} – {end_dt.day} {end_dt.strftime('%b')} {end_dt.year}"

            proposal = Proposal.objects.create(
                category=category,
                proposer=participant,
                title=title
            )

        else:
            title = request.POST.get('title', '').strip()

            if not title:
                return JsonResponse({'success': False, 'error': 'Title is required.'})

            cost = request.POST.get('cost', '').strip()
            link = request.POST.get('link', '').strip()

            proposal = Proposal.objects.create(
                category=category,
                proposer=participant,
                title=title,
                cost=cost if cost else None,
                link=link if link else None
            )

        return JsonResponse({
            'success': True,
            'proposal': {
                'id': proposal.id,
                'title': proposal.title,
                'cost': str(proposal.cost) if proposal.cost else '',
                'link': proposal.link or '',
            },
            'proposals_count': category.proposals.count(),
            'max_proposals': category.max_proposals,
        })

    return redirect('trip_detail', pk=trip_pk)

@login_required
def vote_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    trip = proposal.category.trip
    participant = get_object_or_404(TripParticipant, trip=trip, user=request.user)
    if request.method == 'POST':
        score = request.POST.get('score')
        if score and score.isdigit() and 1 <= int(score) <= 5:
            Vote.objects.update_or_create(participant=participant, proposal=proposal, defaults={'score': int(score)})
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        avg_score = proposal.votes.aggregate(Avg('score'))['score__avg'] or 0
        total_votes = proposal.votes.count()
        return JsonResponse({'success': True, 'avg_score': avg_score, 'total_votes': total_votes})
    return redirect('trip_detail', pk=trip.pk)

@login_required
def lock_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    if proposal.category.trip.leader != request.user:
        return JsonResponse({'success': False, 'error': 'Only the leader can lock.'}, status=403)
    proposal.is_locked = True
    proposal.save()

    category = proposal.category
    locked_titles = list(category.proposals.filter(is_locked=True).order_by('created_at').values_list('title', flat=True))

    return JsonResponse({
        'success': True,
        'is_locked': True,
        'summary_update': {
            'category_name': category.name,
            'titles': locked_titles,
        }
    })
@login_required
def unlock_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    if proposal.category.trip.leader != request.user:
        return JsonResponse({'success': False, 'error': 'Only the leader can unlock.'}, status=403)
    proposal.is_locked = False
    proposal.save()

    category = proposal.category
    locked_titles = list(category.proposals.filter(is_locked=True).order_by('created_at').values_list('title', flat=True))

    return JsonResponse({
        'success': True,
        'is_locked': False,
        'summary_update': {
            'category_name': category.name,
            'titles': locked_titles,
        }
    })

@login_required
def edit_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    trip = proposal.category.trip
    if trip.leader != request.user:
        return redirect('trip_detail', pk=trip.pk)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if title:
            proposal.title = title
            proposal.save()
            return redirect('trip_detail', pk=trip.pk)
    return render(request, 'edit_proposal.html', {'proposal': proposal})

@login_required
def send_invites(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if trip.leader != request.user:
        error_message = "Only the trip leader can send invitations."

        if is_ajax:
            return JsonResponse({'success': False, 'error': error_message}, status=403)

        messages.error(request, error_message)
        return redirect('trip_detail', pk=pk)

    if request.method == 'POST':
        emails_raw = request.POST.get('emails', '')
        email_list = [e.strip() for e in emails_raw.split(',') if e.strip()]

        if not email_list:
            error_message = "No valid email addresses provided."

            if is_ajax:
                return JsonResponse({'success': False, 'error': error_message})

            messages.warning(request, error_message)
            return redirect('trip_detail', pk=pk)

        join_link = request.build_absolute_uri(reverse('join_trip', args=[trip.pk]))

        for email in email_list:
            send_mail(
                subject=f"You're invited to join {trip.title} on Etheria",
                message=(
                    f"Hello!\n\n"
                    f"{request.user.username} has invited you to join the group trip "
                    f"\"{trip.title}\".\n\n"
                    f"Click the link below to join:\n{join_link}\n\n"
                    f"See you there!\n– Etheria"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )

        if len(email_list) == 1:
            success_message = f"Invitation successfully sent to {email_list[0]}."
        else:
            success_message = f"Invitations successfully sent to: {', '.join(email_list)}."

        if is_ajax:
            return JsonResponse({'success': True, 'message': success_message})

        messages.success(request, success_message)
        return redirect('trip_detail', pk=pk)

    return redirect('trip_detail', pk=pk)


def join_trip(request, pk):
    trip = get_object_or_404(Trip, pk=pk)

    if not request.user.is_authenticated:
        login_url = reverse('account_login')
        next_url = reverse('join_trip', args=[trip.pk])
        return redirect(f"{login_url}?{urlencode({'next': next_url})}")

    TripParticipant.objects.get_or_create(
        trip=trip,
        user=request.user,
        defaults={'role': 'member'}
    )

    messages.success(request, f"You've joined {trip.title}!")
    return redirect('trip_detail', pk=trip.pk)

@login_required
def trip_chat(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if not TripParticipant.objects.filter(trip=trip, user=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Not a member.'}, status=403)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            participant = TripParticipant.objects.get(trip=trip, user=request.user)
            Message.objects.create(trip=trip, sender=participant, content=content)
            return JsonResponse({'success': True})

    # GET: επέστρεψε τα τελευταία 50 μηνύματα
    messages = trip.messages.select_related('sender__user').order_by('-created_at')[:50]
    data = [{
        'id': m.id,
        'user': m.sender.user.username,
        'content': m.content,
        'time': m.created_at.strftime('%H:%M'),
    } for m in reversed(messages)]
    return JsonResponse({'success': True, 'messages': data})

def delete_proposal(request, pk):
    proposal = get_object_or_404(Proposal, pk=pk)
    if proposal.category.trip.leader != request.user:
        return JsonResponse({'success': False, 'error': 'Only the leader can delete.'}, status=403)
    if proposal.is_locked:
        return JsonResponse({'success': False, 'error': 'Cannot delete a locked proposal.'})

    category = proposal.category
    proposal.delete()  # <-- ΠΡΟΣΘΕΣΕ ΑΥΤΗ ΤΗ ΓΡΑΜΜΗ

    return JsonResponse({
        'success': True,
        'proposals_count': category.proposals.count(),
        'max_proposals': category.max_proposals,
    })


@login_required
def delete_trip(request, pk):
    trip = get_object_or_404(Trip, pk=pk)
    if trip.leader != request.user:
        messages.error(request, "Only the trip leader can delete this trip.")
        return redirect('my_trips')
    if request.method == 'POST':
        trip.delete()
        messages.success(request, f"Trip '{trip.title}' deleted.")
    return redirect('my_trips')

@login_required
def leave_trip(request, pk):
    trip = get_object_or_404(Trip, pk=pk)

    if trip.leader == request.user:
        messages.error(request, "The creator cannot leave a trip they created. You can delete it instead.")
        return redirect('trip_detail', pk=trip.pk)

    if request.method == 'POST':
        TripParticipant.objects.filter(
            trip=trip,
            user=request.user
        ).delete()

        messages.success(request, f"You left {trip.title}.")
        return redirect('my_trips')

    return redirect('trip_detail', pk=trip.pk)