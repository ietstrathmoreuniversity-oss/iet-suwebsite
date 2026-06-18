from django.db import models
from django.utils import timezone


class AdminOTP(models.Model):
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']


EVENT_TYPE_CHOICES = [
    ('Workshop', 'Workshop'),
    ('Seminar', 'Seminar'),
    ('Social', 'Social'),
    ('Competition', 'Competition'),
    ('Talk', 'Talk'),
    ('Hackathon', 'Hackathon'),
]

ANNOUNCEMENT_CATEGORY_CHOICES = EVENT_TYPE_CHOICES + [('General', 'General')]

ASSIGNMENT_ROLE_CHOICES = [
    ('Lead Organizer', 'Lead Organizer'),
    ('Logistics', 'Logistics'),
    ('Registration', 'Registration'),
    ('MC', 'MC'),
    ('Technical Support', 'Technical Support'),
]

PERMISSION_CHOICES = [
    ('Admin', 'Admin'),
    ('Coordinator', 'Coordinator'),
    ('View-Only', 'View-Only'),
]

PHOTO_TYPE_CHOICES = [
    ('header', 'Header Photo'),
    ('looking_back', 'Looking Back'),
    ('partners', 'Partners'),
]

GALLERY_CATEGORY_CHOICES = [
    ('Symposium', 'Symposium'),
    ('Open day', 'Open day'),
    ('Site visit', 'Site visit'),
    ('Panel', 'Panel'),
    ('Recurring', 'Recurring'),
    ('Milestone', 'Milestone'),
    ('Hackathon', 'Hackathon'),
    ('Other', 'Other'),
]

YEAR_CHOICES = [(i, f'Year {i}') for i in range(1, 6)]


class Official(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    role_title = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='officials/', blank=True, null=True)
    permission_level = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='Coordinator')
    is_active = models.BooleanField(default=True)
    quote = models.TextField(blank=True)
    course = models.CharField(max_length=200, blank=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_order', 'full_name']

    @property
    def initials(self):
        parts = self.full_name.strip().split()
        return ''.join(p[0].upper() for p in parts[:2]) if parts else '?'

    def __str__(self):
        return self.full_name


class Event(models.Model):
    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='Workshop')
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)
    venue = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='events/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=[('Published', 'Published'), ('Draft', 'Draft')], default='Draft')
    show_on_landing = models.BooleanField(default=True)
    seats_total = models.PositiveIntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    @property
    def temporal_status(self):
        today = timezone.localdate()
        if self.date > today:
            return 'Upcoming'
        if self.date == today:
            return 'Ongoing'
        return 'Past'

    def __str__(self):
        return self.title


class EventAssignment(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='assignments')
    official = models.ForeignKey(Official, on_delete=models.CASCADE, related_name='assignments')
    assignment_role = models.CharField(max_length=30, choices=ASSIGNMENT_ROLE_CHOICES, default='Lead Organizer')

    class Meta:
        unique_together = ('event', 'official')

    def __str__(self):
        return f'{self.official} → {self.event} ({self.assignment_role})'


class Member(models.Model):
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=50, blank=True)
    course = models.CharField(max_length=200)
    year_of_study = models.PositiveSmallIntegerField(choices=YEAR_CHOICES, default=1)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']

    @property
    def initials(self):
        parts = self.full_name.strip().split()
        return ''.join(p[0].upper() for p in parts[:2]) if parts else '?'

    def __str__(self):
        return self.full_name


class GalleryItem(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=GALLERY_CATEGORY_CHOICES, default='Other')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='gallery/', blank=True, null=True)
    event_date = models.DateField(blank=True, null=True)
    photo_type = models.CharField(max_length=20, choices=PHOTO_TYPE_CHOICES, default='looking_back')
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['display_order', '-event_date']

    def __str__(self):
        return self.title


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    category = models.CharField(max_length=20, choices=ANNOUNCEMENT_CATEGORY_CHOICES, default='General')
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
