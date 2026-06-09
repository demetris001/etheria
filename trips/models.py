from django.db import models
from django.contrib.auth.models import User
import uuid

class Trip(models.Model):
    TRANSPORT_CHOICES = [
        ('air', 'Αεροπορικώς'),
        ('road', 'Οδικώς'),
        ('sea', 'Πλοίο'),
        ('bus', 'Λεωφορείο'),
        ('train', 'Τρένο'),
        ('custom', 'Άλλο (custom)'),
    ]
    STATUS_CHOICES = [
        ('active', 'Ενεργό'),
        ('completed', 'Ολοκληρωμένο'),
        ('cancelled', 'Ακυρωμένο'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    origin = models.CharField(max_length=200, blank=True, null=True)
    destination = models.CharField(max_length=200, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, default='air', blank=True)
    transport_custom = models.CharField(max_length=200, blank=True, null=True)
    budget_per_person = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_participants = models.PositiveIntegerField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    invite_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_trips')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
class TripParticipant(models.Model):
    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('member', 'Member'),
    ]
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_participations')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('trip', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.trip.title} as {self.role}"


class Category(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=200)
    max_proposals = models.PositiveIntegerField(default=10)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return f"{self.name} ({self.trip.title})"


class Proposal(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='proposals')
    proposer = models.ForeignKey(TripParticipant, on_delete=models.CASCADE, related_name='proposals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} by {self.proposer.user.username}"


class Vote(models.Model):
    participant = models.ForeignKey(TripParticipant, on_delete=models.CASCADE, related_name='votes')
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='votes')
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('participant', 'proposal')

    def __str__(self):
        return f"{self.participant.user.username} voted {self.score} for {self.proposal.title}"


class DayPlan(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='day_plans')
    title = models.CharField(max_length=200)
    date = models.DateField()
    order = models.PositiveIntegerField()
    max_activities = models.PositiveIntegerField(default=4)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.trip.title} - {self.title}"


class Activity(models.Model):
    day_plan = models.ForeignKey(DayPlan, on_delete=models.CASCADE, related_name='activities')
    proposer = models.ForeignKey(TripParticipant, on_delete=models.CASCADE, related_name='activities')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} ({self.day_plan.title})"


class ActivityVote(models.Model):
    participant = models.ForeignKey(TripParticipant, on_delete=models.CASCADE, related_name='activity_votes')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='votes')
    score = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = ('participant', 'activity')

    def __str__(self):
        return f"{self.participant.user.username} voted {self.score} for {self.activity.title}"


class Message(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(TripParticipant, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.user.username}: {self.content[:50]}..."
