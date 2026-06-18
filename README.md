# IET Strathmore Student Chapter

Official website for the Institution of Engineering and Technology (IET) Student Chapter at Strathmore University, Nairobi.

## Overview

A full-stack Django web application with a public-facing landing page and a password-protected admin dashboard for chapter management.

## Features

### Landing Page
- Upcoming events pulled live from the database
- Leadership team with photos
- Past events gallery
- Published announcements banner
- Live active member count

### Admin Dashboard
- OTP-only login (no password stored)
- Manage **Events** — create, schedule, assign officials, set visibility on landing page
- Manage **Officials** — add team members with photos, roles, and quotes
- Manage **Members** — track active chapter members
- Manage **Gallery** — upload past event photos
- Manage **Announcements** — publish notices to the landing page
- Email notification sent to an official when assigned to an event

## Tech Stack

- **Backend**: Django 5.2 (Python 3.11)
- **Database**: SQLite3
- **Frontend**: Vanilla HTML/CSS/JS (no framework)
- **Auth**: Session-based OTP login
- **Email**: Django SMTP via `send_mail`

## Project Structure

```
IET Strathmore Chapter/
├── core/
│   ├── models.py        # Official, Event, Member, GalleryItem, Announcement
│   ├── views.py         # Page views + REST-style API endpoints
│   ├── urls.py          # Page routes
│   └── api_urls.py      # /api/* routes
├── templates/
│   └── core/
│       ├── index.html         # Landing page
│       ├── admin-login.html   # OTP login
│       └── admin-dashboard.html
├── static/
│   ├── css/
│   │   ├── styles.css         # Landing page styles
│   │   └── admin-dashboard.css
│   └── js/
│       ├── script.js          # Landing page JS
│       └── admin-dashboard.js
└── iet_strathmore/
    ├── settings.py
    └── urls.py
```

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/James-Muthama-Mailu/IET-Strathmore-Chapter.git
cd IET-Strathmore-Chapter
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install django pillow python-decouple djangorestframework
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the landing page and `http://127.0.0.1:8000/admin-login/` for the dashboard.

## Admin Access

The dashboard uses OTP-only login — no password is stored. An OTP is sent to the configured admin email when requested. The code expires after 10 minutes.

## API Endpoints

All endpoints are under `/api/` and require an active admin session.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/events/` | List or create events |
| GET/POST/DELETE | `/api/events/<id>/` | Get, update, or delete an event |
| GET/POST | `/api/officials/` | List or create officials |
| GET/POST/DELETE | `/api/officials/<id>/` | Get, update, or delete an official |
| GET/POST | `/api/members/` | List or create members |
| GET/POST/DELETE | `/api/members/<id>/` | Get, update, or delete a member |
| GET/POST | `/api/gallery/` | List or create gallery items |
| GET/POST/DELETE | `/api/gallery/<id>/` | Get, update, or delete a gallery item |
| GET/POST | `/api/announcements/` | List or create announcements |
| GET/POST/DELETE | `/api/announcements/<id>/` | Get, update, or delete an announcement |
| GET | `/api/stats/` | Dashboard stat counts |
