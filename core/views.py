import json
import random
import string
from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import (
    AdminOTP, Announcement, Event, EventAssignment,
    GalleryItem, Member, Official,
)

ADMIN_EMAIL = 'iet.strathmoreuniversity@gmail.com'


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

def admin_api(view_func):
    @wraps(view_func)
    def _wrapper(request, *args, **kwargs):
        if not request.session.get('is_admin'):
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapper


# ---------------------------------------------------------------------------
# Serialisers
# ---------------------------------------------------------------------------

def _ser_official(o):
    return {
        'id': o.id,
        'full_name': o.full_name,
        'email': o.email,
        'role_title': o.role_title,
        'photo': o.photo.url if o.photo else None,
        'permission_level': o.permission_level,
        'is_active': o.is_active,
        'quote': o.quote,
        'course': o.course,
        'display_order': o.display_order,
        'initials': o.initials,
        'active_assignments': o.assignments.count(),
    }


def _ser_event(e):
    return {
        'id': e.id,
        'title': e.title,
        'event_type': e.event_type,
        'date': e.date.isoformat(),
        'time': e.time.strftime('%H:%M') if e.time else '',
        'venue': e.venue,
        'description': e.description,
        'cover_image': e.cover_image.url if e.cover_image else None,
        'status': e.status,
        'show_on_landing': e.show_on_landing,
        'seats_total': e.seats_total,
        'temporal_status': e.temporal_status,
        'assignments': [
            {
                'official_id': a.official_id,
                'official_name': a.official.full_name,
                'initials': a.official.initials,
                'role': a.assignment_role,
            }
            for a in e.assignments.select_related('official').all()
        ],
    }


def _ser_member(m):
    return {
        'id': m.id,
        'full_name': m.full_name,
        'email': m.email,
        'student_id': m.student_id,
        'course': m.course,
        'year_of_study': m.year_of_study,
        'is_active': m.is_active,
        'joined_at': m.joined_at.isoformat(),
        'initials': m.initials,
    }


def _ser_gallery(g):
    return {
        'id': g.id,
        'title': g.title,
        'category': g.category,
        'description': g.description,
        'image': g.image.url if g.image else None,
        'event_date': g.event_date.isoformat() if g.event_date else None,
        'photo_type': g.photo_type,
        'display_order': g.display_order,
    }


def _ser_announcement(a):
    return {
        'id': a.id,
        'title': a.title,
        'body': a.body,
        'category': a.category,
        'is_published': a.is_published,
        'created_at': a.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Page views
# ---------------------------------------------------------------------------

def home(request):
    today = timezone.localdate()
    events = Event.objects.filter(
        status='Published', show_on_landing=True, date__gte=today
    ).order_by('date', 'time')[:3]
    officials = Official.objects.filter(is_active=True).order_by('display_order', 'full_name')
    header_photo = GalleryItem.objects.filter(photo_type='header').order_by('display_order').first()
    looking_back_items = GalleryItem.objects.filter(photo_type='looking_back').order_by('-event_date', '-id')
    partner_items = GalleryItem.objects.filter(photo_type='partners').order_by('display_order', 'id')
    announcements = Announcement.objects.filter(is_published=True).order_by('-created_at')[:3]
    member_count = Member.objects.filter(is_active=True).count()
    return render(request, 'core/index.html', {
        'events': events,
        'officials': officials,
        'header_photo': header_photo,
        'looking_back_items': looking_back_items,
        'partner_items': partner_items,
        'announcements': announcements,
        'member_count': member_count,
    })


def admin_login(request):
    if request.session.get('is_admin'):
        return redirect('admin_dashboard')
    officials = Official.objects.filter(is_active=True).order_by('display_order', 'full_name')
    return render(request, 'core/admin-login.html', {
        'officials': officials,
    })


@require_POST
def request_otp(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

    official_id = data.get('official_id')
    if not official_id:
        return JsonResponse({'success': False, 'error': 'Please select your role before sending a code.'}, status=400)

    if official_id == 'superuser':
        email = ADMIN_EMAIL
        official_name = 'Superuser'
        official_role = 'Default Admin'
        login_official_id = 'superuser'
    else:
        try:
            official = Official.objects.get(pk=official_id, is_active=True)
        except Official.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Selected official is not valid.'}, status=400)
        email = official.email
        official_name = official.full_name
        official_role = official.role_title
        login_official_id = official.id

    AdminOTP.objects.filter(used=False).update(used=True)
    code = ''.join(random.choices(string.digits, k=6))
    expires_at = timezone.now() + timedelta(minutes=10)
    AdminOTP.objects.create(code=code, expires_at=expires_at)
    request.session['login_official_id'] = login_official_id
    request.session['official_name'] = official_name
    request.session['official_role'] = official_role
    otp_plain = (
        f'Hi {official_name},\n\n'
        f'Your IET Strathmore admin login code is: {code}\n\n'
        f'This code expires in 10 minutes.\n\n'
        f'If you did not request this, please ignore this email.\n\n'
        f'IET Strathmore Chapter Admin Team'
    )

    otp_body = f"""
      <p style="margin:0 0 22px;font-size:15px;line-height:1.6;color:#4b3a4d;">
        A login was requested for the <strong style="color:#53264d;">IET Strathmore Chapter</strong>
        admin dashboard. Use the code below to complete sign-in.
      </p>

      <!-- OTP code block -->
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;">
        <tr>
          <td align="center">
            <div style="display:inline-block;background:linear-gradient(135deg,#1a0a18,#53264d);
                        border-radius:14px;padding:28px 48px;">
              <p style="margin:0 0 8px;font-size:11px;letter-spacing:.2em;text-transform:uppercase;
                         font-weight:700;color:#CB9D51;">Your login code</p>
              <p style="margin:0;font-family:'Courier New',monospace;font-size:44px;font-weight:900;
                         letter-spacing:.18em;color:#ffffff;line-height:1;">{code}</p>
              <p style="margin:10px 0 0;font-size:12px;color:rgba(255,255,255,.55);">
                Expires in 10 minutes
              </p>
            </div>
          </td>
        </tr>
      </table>

      <p style="margin:0 0 16px;font-size:15px;line-height:1.65;color:#4b3a4d;">
        Enter this code on the admin login page to access the dashboard.
      </p>
      <p style="margin:0 0 28px;font-size:13px;line-height:1.6;color:#9a8a9c;">
        If you did not request this code, you can safely ignore this email.
        Someone may have entered your email address by mistake.
      </p>

      <div style="border-top:2px solid #e7d9e8;padding-top:20px;">
        <p style="margin:0;font-size:14px;font-weight:700;color:#53264d;">IET Strathmore Chapter Admin Team</p>
        <p style="margin:4px 0 0;font-size:13px;color:#9a8a9c;">{ADMIN_EMAIL}</p>
      </div>"""

    otp_html = _email_wrap('IET Strathmore · Admin Access', 'Your one-time<br>login code.', otp_body)

    try:
        send_mail(
            subject=f'IET Strathmore Admin Login Code for {official_name}',
            message=otp_plain,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            html_message=otp_html,
            fail_silently=False,
        )
    except Exception:
        return JsonResponse(
            {'success': False, 'error': 'Failed to send email. Check server email configuration.'},
            status=500,
        )
    return JsonResponse({'success': True})


@require_POST
def verify_otp(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)
    code = data.get('code', '').strip()
    if len(code) != 6 or not code.isdigit():
        return JsonResponse({'success': False, 'error': 'Invalid code format'}, status=400)
    login_official_id = request.session.get('login_official_id')
    if not login_official_id:
        return JsonResponse({'success': False, 'error': 'Session expired. Please request a new code.'}, status=400)
    now = timezone.now()
    try:
        otp = AdminOTP.objects.filter(code=code, used=False, expires_at__gt=now).latest('created_at')
        otp.used = True
        otp.save()
        request.session['is_admin'] = True
        request.session['official_id'] = login_official_id
        request.session.pop('login_official_id', None)
        try:
            official = Official.objects.get(pk=login_official_id)
            request.session['official_name'] = official.full_name
            request.session['official_role'] = official.role_title
        except Official.DoesNotExist:
            request.session['official_name'] = 'Admin'
            request.session['official_role'] = 'Chapter Admin'
        request.session.set_expiry(3600 * 8)
        return JsonResponse({'success': True})
    except AdminOTP.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid or expired code'}, status=400)


def admin_dashboard(request):
    if not request.session.get('is_admin'):
        return redirect('admin_login')
    official_name = request.session.get('official_name', 'Admin')
    official_role = request.session.get('official_role', 'Chapter Admin')
    return render(request, 'core/admin-dashboard.html', {
        'official_name': official_name,
        'official_role': official_role,
    })


def admin_logout(request):
    request.session.flush()
    return redirect('admin_login')


# ---------------------------------------------------------------------------
# API: Stats
# ---------------------------------------------------------------------------

@admin_api
def api_stats(request):
    today = timezone.localdate()
    from django.utils import timezone as tz
    import datetime
    month_start = today.replace(day=1)
    return JsonResponse({
        'total_events': Event.objects.count(),
        'upcoming_events': Event.objects.filter(date__gt=today).count(),
        'ongoing_events': Event.objects.filter(date=today).count(),
        'past_events': Event.objects.filter(date__lt=today).count(),
        'total_members': Member.objects.count(),
        'active_members': Member.objects.filter(is_active=True).count(),
        'new_members_this_month': Member.objects.filter(joined_at__gte=month_start).count(),
        'total_officials': Official.objects.count(),
        'active_officials': Official.objects.filter(is_active=True).count(),
        'published_announcements': Announcement.objects.filter(is_published=True).count(),
        'total_gallery': GalleryItem.objects.count(),
    })


# ---------------------------------------------------------------------------
# API: Events
# ---------------------------------------------------------------------------

@admin_api
def api_events(request):
    if request.method == 'GET':
        qs = Event.objects.prefetch_related('assignments__official').all()
        return JsonResponse([_ser_event(e) for e in qs], safe=False)

    if request.method == 'POST':
        try:
            e = Event(
                title=request.POST.get('title', '').strip(),
                event_type=request.POST.get('event_type', 'Workshop'),
                date=request.POST.get('date'),
                time=request.POST.get('time') or None,
                venue=request.POST.get('venue', '').strip(),
                description=request.POST.get('description', '').strip(),
                status=request.POST.get('status', 'Draft'),
                show_on_landing=request.POST.get('show_on_landing') == '1',
                seats_total=int(request.POST['seats_total']) if request.POST.get('seats_total') else None,
            )
            if 'cover_image' in request.FILES:
                e.cover_image = request.FILES['cover_image']
            e.save()
            e.refresh_from_db()
            _save_assignments(e, request.POST.get('assignments', '[]'))
            e = Event.objects.prefetch_related('assignments__official').get(pk=e.pk)
            return JsonResponse(_ser_event(e), status=201)
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@admin_api
def api_event_detail(request, pk):
    try:
        e = Event.objects.prefetch_related('assignments__official').get(pk=pk)
    except Event.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'GET':
        return JsonResponse(_ser_event(e))

    if request.method == 'POST':
        try:
            e.title = request.POST.get('title', e.title).strip()
            e.event_type = request.POST.get('event_type', e.event_type)
            e.date = request.POST.get('date', e.date)
            e.time = request.POST.get('time') or None
            e.venue = request.POST.get('venue', e.venue).strip()
            e.description = request.POST.get('description', e.description).strip()
            e.status = request.POST.get('status', e.status)
            e.show_on_landing = request.POST.get('show_on_landing') == '1'
            if request.POST.get('seats_total'):
                e.seats_total = int(request.POST['seats_total'])
            if 'cover_image' in request.FILES:
                e.cover_image = request.FILES['cover_image']
            e.save()
            e.refresh_from_db()
            _save_assignments(e, request.POST.get('assignments', '[]'))
            e = Event.objects.prefetch_related('assignments__official').get(pk=e.pk)
            return JsonResponse(_ser_event(e))
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    if request.method == 'DELETE':
        e.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def _save_assignments(event, assignments_json):
    try:
        assignments = json.loads(assignments_json)
    except (json.JSONDecodeError, TypeError):
        return

    # Capture who was already assigned before any changes
    existing_ids = set(event.assignments.values_list('official_id', flat=True))

    # Build map of official_id -> role from the incoming payload
    new_map = {}
    for a in assignments:
        oid = a.get('official_id') or a.get('id')
        if oid:
            new_map[int(oid)] = a.get('role', 'Lead Organizer')

    # Remove assignments that are no longer in the list
    event.assignments.exclude(official_id__in=new_map.keys()).delete()

    # Create/update each assignment; email only genuinely new additions
    for official_id, role in new_map.items():
        EventAssignment.objects.update_or_create(
            event=event,
            official_id=official_id,
            defaults={'assignment_role': role},
        )
        if official_id not in existing_ids:
            try:
                official = Official.objects.get(pk=official_id)
                _send_assignment_email(official, event, role)
            except Official.DoesNotExist:
                pass


def _send_assignment_email(official, event, role):
    date_str = event.date.strftime('%A, %d %B %Y')
    time_str = event.time.strftime('%I:%M %p') if event.time else 'TBD'
    venue = event.venue or 'TBD'

    subject = f'Event Assignment: {role} — {event.title}'

    plain = (
        f'Hi {official.full_name},\n\n'
        f'You have been assigned to an upcoming IET Strathmore Chapter event.\n\n'
        f'Event : {event.title}\n'
        f'Date  : {date_str}\n'
        f'Time  : {time_str}\n'
        f'Venue : {venue}\n'
        f'Role  : {role}\n'
    )
    if event.description:
        plain += f'\nAbout this event:\n{event.description}\n'
    plain += (
        f'\nPlease ensure you are available and prepared for your role on the day.\n\n'
        f'Thank you for your contribution to IET Strathmore.\n\n'
        f'IET Strathmore Chapter Admin Team\n{ADMIN_EMAIL}'
    )

    desc_block = ''
    if event.description:
        desc_block = f"""
        <tr>
          <td style="padding:14px 24px 20px;font-size:14px;line-height:1.65;color:#4b3a4d;border-top:1px solid #e7d9e8;">
            <p style="margin:0 0 6px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;font-weight:700;color:#9a8a9c;">About this event</p>
            {event.description}
          </td>
        </tr>"""

    info_rows = (
        _info_row('Event', event.title) +
        _info_row('Date', date_str) +
        _info_row('Time', time_str) +
        _info_row('Venue', venue) +
        _info_row('Your Role', role)
    )

    body = f"""
      <p style="margin:0 0 20px;font-size:16px;color:#1e1320;">Hi <strong>{official.full_name}</strong>,</p>
      <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#4b3a4d;">
        You have been assigned to an upcoming
        <strong style="color:#53264d;">IET Strathmore Chapter</strong> event.
        Here are the details:
      </p>

      <!-- Event details card -->
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#f9f4fa;border-radius:10px;border:1px solid #e7d9e8;margin-bottom:28px;">
        <tbody>
          {info_rows}
          {desc_block}
        </tbody>
      </table>

      <p style="margin:0 0 28px;font-size:15px;line-height:1.65;color:#4b3a4d;">
        Please ensure you are available and prepared for your role on the day. If you have any
        questions or need to flag a conflict, reply to this email or reach out to the admin team.
      </p>

      <div style="border-top:2px solid #e7d9e8;padding-top:20px;">
        <p style="margin:0;font-size:14px;font-weight:700;color:#53264d;">IET Strathmore Chapter Admin Team</p>
        <p style="margin:4px 0 0;font-size:13px;color:#9a8a9c;">{ADMIN_EMAIL}</p>
      </div>"""

    html = _email_wrap(f'IET Strathmore · {event.event_type}', f'You\'ve been assigned:<br>{role}.', body)

    try:
        send_mail(
            subject=subject,
            message=plain,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[official.email],
            html_message=html,
            fail_silently=True,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Welcome emails
# ---------------------------------------------------------------------------

def _email_wrap(header_label, title, body_html):
    """Wrap content in the IET Strathmore branded email shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1e6f2;font-family:'Inter',Arial,sans-serif;color:#1e1320;">

  <!-- Wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f1e6f2;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 8px 32px rgba(83,38,77,.15);">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#1a0a18 0%,#53264d 60%,#964f9f 100%);padding:36px 40px 28px;">
            <p style="margin:0 0 6px;font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:#CB9D51;font-weight:700;">{header_label}</p>
            <h1 style="margin:0;font-size:26px;font-weight:800;color:#ffffff;line-height:1.15;letter-spacing:-.02em;">{title}</h1>
            <!-- Gold accent line -->
            <div style="margin-top:20px;height:2px;width:48px;background:#CB9D51;border-radius:2px;"></div>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:36px 40px;">
            {body_html}
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#1a0a18;padding:24px 40px;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td>
                  <p style="margin:0;font-size:13px;font-weight:700;color:#CB9D51;letter-spacing:.06em;text-transform:uppercase;">IET Strathmore Student Chapter</p>
                  <p style="margin:4px 0 0;font-size:12px;color:rgba(255,255,255,.55);">Strathmore University · Nairobi, Kenya</p>
                </td>
                <td align="right" style="vertical-align:top;">
                  <a href="mailto:{ADMIN_EMAIL}" style="font-size:12px;color:#CB9D51;text-decoration:none;">{ADMIN_EMAIL}</a>
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>

      <!-- Sub-footer note -->
      <p style="margin:18px 0 0;font-size:11px;color:#9a7a9c;text-align:center;">
        You are receiving this email because you were added to the IET Strathmore Chapter.
      </p>
    </td></tr>
  </table>

</body>
</html>"""


def _info_row(label, value):
    return f"""
    <tr>
      <td style="padding:10px 14px;font-size:12px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:#53264d;white-space:nowrap;width:1%;">{label}</td>
      <td style="padding:10px 14px;font-size:14px;color:#1e1320;font-weight:500;">{value}</td>
    </tr>"""


def _send_official_welcome(official):
    subject = 'Welcome to IET Strathmore Chapter — You\'ve Been Added as an Official'

    plain = (
        f'Hi {official.full_name},\n\n'
        f'Congratulations! You have been added as an official of the IET Strathmore University Student Chapter.\n\n'
        f'Role: {official.role_title}\n'
        f'Permission: {official.permission_level}\n\n'
        f'As a chapter official you are part of a team driving engineering excellence at Strathmore University. '
        f'Your role is key to building a community that connects students to the global engineering profession.\n\n'
        f'If you have any questions, reach out to us at {ADMIN_EMAIL}.\n\n'
        f'Welcome aboard,\nIET Strathmore Chapter Admin Team'
    )

    info_rows = _info_row('Role', official.role_title) + _info_row('Permission Level', official.permission_level)
    if official.course:
        info_rows += _info_row('Course', official.course)

    body = f"""
      <p style="margin:0 0 20px;font-size:16px;color:#1e1320;">Hi <strong>{official.full_name}</strong>,</p>
      <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#4b3a4d;">
        Congratulations — you have been added as an official of the
        <strong style="color:#53264d;">IET Strathmore University Student Chapter</strong>.
        Welcome to the team.
      </p>

      <!-- Info table -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9f4fa;border-radius:10px;border:1px solid #e7d9e8;margin-bottom:28px;">
        <tbody>{info_rows}</tbody>
      </table>

      <p style="margin:0 0 16px;font-size:15px;line-height:1.65;color:#4b3a4d;">
        As a chapter official you are part of a team driving engineering excellence at Strathmore University.
        Your role is key to building a community that connects students to the global engineering profession.
      </p>
      <p style="margin:0 0 28px;font-size:15px;line-height:1.65;color:#4b3a4d;">
        If you have any questions or need to flag anything, reply to this email or reach out to the
        admin team directly.
      </p>

      <!-- Sign-off -->
      <div style="border-top:2px solid #e7d9e8;padding-top:20px;">
        <p style="margin:0;font-size:14px;font-weight:700;color:#53264d;">IET Strathmore Chapter Admin Team</p>
        <p style="margin:4px 0 0;font-size:13px;color:#9a8a9c;">{ADMIN_EMAIL}</p>
      </div>"""

    html = _email_wrap('IET Strathmore · Official', 'Welcome aboard,<br>Chapter Official.', body)

    try:
        send_mail(
            subject=subject,
            message=plain,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[official.email],
            html_message=html,
            fail_silently=True,
        )
    except Exception:
        pass


def _send_member_welcome(member):
    subject = 'Welcome to IET Strathmore Chapter!'

    plain = (
        f'Hi {member.full_name},\n\n'
        f'Welcome to the IET Strathmore University Student Chapter!\n\n'
        f'Student ID: {member.student_id or "N/A"}\n'
        f'Course: {member.course}\n'
        f'Year: Year {member.year_of_study}\n\n'
        f'As a member you now have access to chapter events, workshops, and industry talks.\n\n'
        f'Keep an eye on your inbox for upcoming event announcements. '
        f'Follow us on Instagram @iet.strathmore for the latest updates.\n\n'
        f'If you have any questions, reach out to us at {ADMIN_EMAIL}.\n\n'
        f'Welcome to the chapter,\nIET Strathmore Chapter Admin Team'
    )

    info_rows = _info_row('Student ID', member.student_id or 'N/A') + \
                _info_row('Course', member.course) + \
                _info_row('Year of Study', f'Year {member.year_of_study}')

    body = f"""
      <p style="margin:0 0 20px;font-size:16px;color:#1e1320;">Hi <strong>{member.full_name}</strong>,</p>
      <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#4b3a4d;">
        Welcome to the <strong style="color:#53264d;">IET Strathmore University Student Chapter</strong>!
        We're excited to have you with us.
      </p>

      <!-- Info table -->
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f9f4fa;border-radius:10px;border:1px solid #e7d9e8;margin-bottom:28px;">
        <tbody>{info_rows}</tbody>
      </table>

      <p style="margin:0 0 16px;font-size:15px;line-height:1.65;color:#4b3a4d;">
        As a member you now have access to chapter events, workshops, and industry talks.
      </p>
      <p style="margin:0 0 28px;font-size:15px;line-height:1.65;color:#4b3a4d;">
        Keep an eye on your inbox for upcoming event announcements. You can also follow us on
        Instagram <strong style="color:#53264d;">@iet.strathmore</strong> for the latest updates.
      </p>

      <!-- Sign-off -->
      <div style="border-top:2px solid #e7d9e8;padding-top:20px;">
        <p style="margin:0;font-size:14px;font-weight:700;color:#53264d;">IET Strathmore Chapter Admin Team</p>
        <p style="margin:4px 0 0;font-size:13px;color:#9a8a9c;">{ADMIN_EMAIL}</p>
      </div>"""

    html = _email_wrap('IET Strathmore · Membership', 'Welcome to the<br>Chapter.', body)

    try:
        send_mail(
            subject=subject,
            message=plain,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[member.email],
            html_message=html,
            fail_silently=True,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# API: Officials
# ---------------------------------------------------------------------------

@admin_api
def api_officials(request):
    if request.method == 'GET':
        return JsonResponse([_ser_official(o) for o in Official.objects.all()], safe=False)

    if request.method == 'POST':
        try:
            email = request.POST.get('email', '').strip()
            if Official.objects.filter(email__iexact=email).exists():
                return JsonResponse({'error': 'An official with this email already exists.'}, status=409)
            o = Official(
                full_name=request.POST.get('full_name', '').strip(),
                email=email,
                role_title=request.POST.get('role_title', '').strip(),
                permission_level=request.POST.get('permission_level', 'Coordinator'),
                is_active=True,
                quote=request.POST.get('quote', '').strip(),
                course=request.POST.get('course', '').strip(),
                display_order=int(request.POST.get('display_order', 0) or 0),
            )
            if 'photo' in request.FILES:
                o.photo = request.FILES['photo']
            o.save()
            _send_official_welcome(o)
            return JsonResponse(_ser_official(o), status=201)
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@admin_api
def api_official_detail(request, pk):
    try:
        o = Official.objects.get(pk=pk)
    except Official.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        try:
            new_email = request.POST.get('email', o.email).strip()
            if new_email.lower() != o.email.lower() and Official.objects.filter(email__iexact=new_email).exists():
                return JsonResponse({'error': 'An official with this email already exists.'}, status=409)
            o.full_name = request.POST.get('full_name', o.full_name).strip()
            o.email = new_email
            o.role_title = request.POST.get('role_title', o.role_title).strip()
            o.permission_level = request.POST.get('permission_level', o.permission_level)
            o.quote = request.POST.get('quote', o.quote).strip()
            o.course = request.POST.get('course', o.course).strip()
            o.is_active = request.POST.get('is_active', '1') == '1'
            if 'photo' in request.FILES:
                o.photo = request.FILES['photo']
            o.save()
            return JsonResponse(_ser_official(o))
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    if request.method == 'DELETE':
        o.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ---------------------------------------------------------------------------
# API: Members
# ---------------------------------------------------------------------------

@admin_api
def api_members(request):
    if request.method == 'GET':
        return JsonResponse([_ser_member(m) for m in Member.objects.all()], safe=False)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            if Member.objects.filter(email__iexact=email).exists():
                return JsonResponse({'error': 'A member with this email already exists.'}, status=409)
            m = Member.objects.create(
                full_name=data.get('full_name', '').strip(),
                email=email,
                student_id=data.get('student_id', '').strip(),
                course=data.get('course', '').strip(),
                year_of_study=int(data.get('year_of_study', 1)),
                is_active=True,
            )
            _send_member_welcome(m)
            return JsonResponse(_ser_member(m), status=201)
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@admin_api
def api_member_detail(request, pk):
    try:
        m = Member.objects.get(pk=pk)
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_email = data.get('email', m.email).strip()
            if new_email.lower() != m.email.lower() and Member.objects.filter(email__iexact=new_email).exists():
                return JsonResponse({'error': 'A member with this email already exists.'}, status=409)
            m.full_name = data.get('full_name', m.full_name).strip()
            m.email = new_email
            m.student_id = data.get('student_id', m.student_id).strip()
            m.course = data.get('course', m.course).strip()
            m.year_of_study = int(data.get('year_of_study', m.year_of_study))
            m.is_active = data.get('is_active', m.is_active)
            m.save()
            return JsonResponse(_ser_member(m))
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    if request.method == 'DELETE':
        m.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ---------------------------------------------------------------------------
# API: Gallery
# ---------------------------------------------------------------------------

@admin_api
def api_gallery(request):
    if request.method == 'GET':
        return JsonResponse([_ser_gallery(g) for g in GalleryItem.objects.all()], safe=False)

    if request.method == 'POST':
        try:
            g = GalleryItem(
                title=request.POST.get('title', '').strip(),
                category=request.POST.get('category', 'Other'),
                description=request.POST.get('description', '').strip(),
                event_date=request.POST.get('event_date') or None,
                photo_type=request.POST.get('photo_type', 'looking_back'),
                display_order=int(request.POST.get('display_order', 0) or 0),
            )
            if 'image' in request.FILES:
                g.image = request.FILES['image']
            g.save()
            g.refresh_from_db()
            return JsonResponse(_ser_gallery(g), status=201)
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@admin_api
def api_gallery_detail(request, pk):
    try:
        g = GalleryItem.objects.get(pk=pk)
    except GalleryItem.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        try:
            g.title = request.POST.get('title', g.title).strip()
            g.category = request.POST.get('category', g.category)
            g.description = request.POST.get('description', g.description).strip()
            if request.POST.get('event_date'):
                g.event_date = request.POST['event_date']
            g.photo_type = request.POST.get('photo_type', g.photo_type)
            if request.POST.get('display_order') is not None:
                g.display_order = int(request.POST.get('display_order', g.display_order) or 0)
            if 'image' in request.FILES:
                g.image = request.FILES['image']
            g.save()
            g.refresh_from_db()
            return JsonResponse(_ser_gallery(g))
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    if request.method == 'DELETE':
        g.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


def _send_announcement_broadcast(announcement):
    """Send a published announcement to every active member and official."""
    member_emails = list(
        Member.objects.filter(is_active=True).exclude(email='').values_list('email', flat=True)
    )
    official_emails = list(
        Official.objects.filter(is_active=True).exclude(email='').values_list('email', flat=True)
    )
    recipients = list(dict.fromkeys(member_emails + official_emails))  # unique, order preserved

    if not recipients:
        return

    subject = f'IET Strathmore: {announcement.title}'

    # Plain-text fallback
    plain = (
        f'{announcement.title}\n\n'
        f'{announcement.body}\n\n'
        f'—\nIET Strathmore Chapter Admin Team\n{ADMIN_EMAIL}'
    )

    # Body paragraphs — preserve line breaks from the textarea
    body_paragraphs = ''.join(
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.7;color:#4b3a4d;">{line}</p>'
        for line in announcement.body.splitlines()
        if line.strip()
    )

    body_html = f"""
      <p style="margin:0 0 26px;font-size:15px;line-height:1.65;color:#4b3a4d;">
        The IET Strathmore University Student Chapter has a new announcement for you.
      </p>

      <!-- Announcement card -->
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#f9f4fa;border-radius:10px;border:1px solid #e7d9e8;margin-bottom:28px;">
        <tr>
          <td style="padding:22px 24px;border-bottom:1px solid #e7d9e8;">
            <p style="margin:0;font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:#CB9D51;">
              {announcement.category}
            </p>
            <h2 style="margin:6px 0 0;font-size:20px;font-weight:800;color:#53264d;line-height:1.2;letter-spacing:-.01em;">
              {announcement.title}
            </h2>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 24px;">
            {body_paragraphs}
          </td>
        </tr>
      </table>

      <p style="margin:0 0 28px;font-size:14px;line-height:1.6;color:#9a8a9c;font-style:italic;">
        This announcement was sent to all IET Strathmore Chapter members and officials.
      </p>

      <!-- Sign-off -->
      <div style="border-top:2px solid #e7d9e8;padding-top:20px;">
        <p style="margin:0;font-size:14px;font-weight:700;color:#53264d;">IET Strathmore Chapter Admin Team</p>
        <p style="margin:4px 0 0;font-size:13px;color:#9a8a9c;">{ADMIN_EMAIL}</p>
      </div>"""

    html = _email_wrap('IET Strathmore · Announcement', announcement.title, body_html)

    for email in recipients:
        try:
            send_mail(
                subject=subject,
                message=plain,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                html_message=html,
                fail_silently=True,
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# API: Announcements
# ---------------------------------------------------------------------------

@admin_api
def api_announcements(request):
    if request.method == 'GET':
        return JsonResponse([_ser_announcement(a) for a in Announcement.objects.all()], safe=False)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            a = Announcement.objects.create(
                title=data.get('title', '').strip(),
                body=data.get('body', '').strip(),
                category=data.get('category', 'General'),
                is_published=True,
            )
            _send_announcement_broadcast(a)
            return JsonResponse(_ser_announcement(a), status=201)
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@admin_api
def api_announcement_detail(request, pk):
    try:
        a = Announcement.objects.get(pk=pk)
    except Announcement.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            a.title = data.get('title', a.title).strip()
            a.body = data.get('body', a.body).strip()
            a.category = data.get('category', a.category)
            a.is_published = data.get('is_published', a.is_published)
            a.save()
            return JsonResponse(_ser_announcement(a))
        except Exception as exc:
            return JsonResponse({'error': str(exc)}, status=400)

    if request.method == 'DELETE':
        a.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
