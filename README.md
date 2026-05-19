# 🎓 EduLearn LMS — Full-Stack Learning Management System

Production-ready Udemy-style LMS · Django 6 + Bootstrap 5 + Razorpay

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install django pillow reportlab razorpay

# 2. Apply migrations
cd lms_project
python manage.py migrate

# 3. Run server
python manage.py runserver
# → http://127.0.0.1:8000
```

---

## 🔑 Demo Accounts (pre-seeded)

| Role       | Username     | Password   |
|------------|--------------|------------|
| Admin      | `admin`      | `admin123` |
| Instructor | `instructor` | `demo1234` |
| Student    | `student`    | `demo1234` |

---

## 💳 Razorpay Payment Setup

1. Get API keys from https://dashboard.razorpay.com/
2. Edit `lms_project/settings.py`:
   ```python
   RAZORPAY_KEY_ID     = 'rzp_test_YOUR_KEY_ID'
   RAZORPAY_KEY_SECRET = 'YOUR_KEY_SECRET'
   ```
3. See **RAZORPAY_SETUP.md** for full guide + test card details

---

## 📁 Project Structure

```
lms_project/
├── accounts/          ← Custom user, auth (student/instructor/admin)
├── courses/           ← Course CRUD, modules, lessons, reviews, wishlist
├── enrollments/       ← Enroll, lesson progress, resume support
├── quizzes/           ← MCQ quizzes, timer, auto-grading
├── certificates/      ← PDF cert generation via ReportLab + verify URL
├── dashboard/         ← Role dashboards + admin approval workflow
├── payments/          ← Razorpay integration (create order, verify, webhook)
├── static/
│   ├── css/style.css  ← Premium design system (700 lines)
│   └── js/script.js   ← AJAX, video player, quiz engine, toast system
├── templates/         ← 30+ HTML templates
├── lms_project/
│   ├── settings.py    ← Config (DB, media, email, Razorpay keys)
│   └── urls.py
├── RAZORPAY_SETUP.md  ← Step-by-step payment setup guide
└── requirements.txt
```

---

## ✨ Features

**Student** — Browse/search/filter courses · Enroll free or buy paid · HD video with resume · Track progress · MCQ quizzes with timer · PDF certificates · Wishlist · Order history

**Instructor** — Create/edit/delete courses · Build curriculum (video/PDF/text/quiz) · Submit for review · Dashboard with student analytics

**Admin** — Approve/reject courses · Manage users (activate/deactivate) · Platform analytics · Django Admin at `/admin/`

**Payments** — Razorpay modal (UPI/Card/NetBanking/Wallets) · Server-side HMAC signature verification · Webhook support · Auto-enroll on success

---

## 🌐 Key URLs

| URL | Description |
|-----|-------------|
| `/` | Home / Landing |
| `/courses/` | Course catalog |
| `/courses/<slug>/` | Course detail |
| `/enrollments/learn/<slug>/<id>/` | Video learning player |
| `/dashboard/` | Role-based dashboard |
| `/quizzes/<id>/take/` | Quiz |
| `/certificates/<uuid>/download/` | PDF certificate |
| `/payments/checkout/<slug>/` | Razorpay checkout |
| `/payments/verify/` | Payment verification (AJAX) |
| `/payments/webhook/` | Razorpay webhook |
| `/admin/` | Django admin |

---

## 🛠️ Tech Stack

| Layer    | Technology |
|----------|-----------|
| Backend  | Django 6 (Python) |
| Database | SQLite (swap to PostgreSQL for prod) |
| Frontend | Bootstrap 5 + Vanilla JS |
| Payment  | Razorpay (HMAC verified) |
| PDF      | ReportLab |
| Icons    | Bootstrap Icons |
| Fonts    | Google Fonts (Inter, Poppins) |

---

*Built with ❤️ · Django + Bootstrap 5 + Razorpay*
