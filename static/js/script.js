/* ============================================
   EduLearn LMS - Main JavaScript
   ============================================ */

// ── Page Loader ──
document.addEventListener('DOMContentLoaded', () => {
  const loader = document.getElementById('page-loader');
  if (loader) setTimeout(() => loader.classList.add('hidden'), 500);

  initSidebar();
  initToasts();
  initWishlist();
  initNotifications();
  initFormValidation();
  initVideoPlayer();
  initProgressSave();
  initAnimations();
  initSearch();
});

// ── Sidebar Toggle ──
function initSidebar() {
  const sidebar = document.getElementById('lmsSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggleBtn = document.getElementById('sidebarToggle');

  if (!sidebar) return;

  toggleBtn?.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    overlay?.classList.toggle('d-block');
  });

  overlay?.addEventListener('click', () => {
    sidebar.classList.remove('open');
    overlay.classList.remove('d-block');
  });

  // Mark active link
  const current = window.location.pathname;
  sidebar.querySelectorAll('.sidebar-nav-item').forEach(link => {
    const href = link.getAttribute('href');
    if (href && current.startsWith(href) && href !== '/') {
      link.classList.add('active');
    }
  });
}

// ── Toast Notifications ──
function showToast(title, message, type = 'info') {
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const container = document.getElementById('toastContainer') || createToastContainer();

  const toast = document.createElement('div');
  toast.className = 'lms-toast';
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${message ? `<div class="toast-msg">${message}</div>` : ''}
    </div>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;
  container.appendChild(toast);
  setTimeout(() => toast.style.opacity = '0', 3500);
  setTimeout(() => toast.remove(), 4000);
}

function createToastContainer() {
  const c = document.createElement('div');
  c.id = 'toastContainer';
  c.className = 'toast-container';
  document.body.appendChild(c);
  return c;
}

function initToasts() {
  // Convert Django messages to toasts
  document.querySelectorAll('.django-message').forEach(el => {
    const type = el.dataset.type || 'info';
    const msg = el.textContent.trim();
    if (msg) showToast(type === 'success' ? 'Success' : type === 'error' || type === 'danger' ? 'Error' : 'Notice', msg, type === 'danger' ? 'error' : type);
    el.remove();
  });
}

// ── Wishlist Toggle ──
function initWishlist() {
  document.querySelectorAll('.wishlist-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const courseId = btn.dataset.courseId;
      const csrfToken = getCsrfToken();

      try {
        const res = await fetch(`/courses/wishlist/toggle/${courseId}/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await res.json();
        const icon = btn.querySelector('i');
        if (data.added) {
          icon.classList.remove('bi-heart');
          icon.classList.add('bi-heart-fill');
          btn.classList.add('active');
          showToast('Saved!', 'Course added to wishlist', 'success');
        } else {
          icon.classList.remove('bi-heart-fill');
          icon.classList.add('bi-heart');
          btn.classList.remove('active');
          showToast('Removed', 'Course removed from wishlist', 'info');
        }
      } catch { showToast('Error', 'Failed to update wishlist', 'error'); }
    });
  });
}

// ── Notifications ──
function initNotifications() {
  const markReadBtn = document.getElementById('markAllRead');
  markReadBtn?.addEventListener('click', async () => {
    try {
      await fetch('/courses/notifications/mark-read/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' }
      });
      document.querySelectorAll('.notif-item.unread').forEach(el => el.classList.remove('unread'));
      const badge = document.querySelector('.nav-badge');
      if (badge) badge.remove();
    } catch {}
  });
}

// ── Form Validation ──
function initFormValidation() {
  document.querySelectorAll('form[data-validate]').forEach(form => {
    form.addEventListener('submit', (e) => {
      let valid = true;
      form.querySelectorAll('[required]').forEach(field => {
        if (!field.value.trim()) {
          field.classList.add('is-invalid');
          valid = false;
        } else {
          field.classList.remove('is-invalid');
        }
      });
      if (!valid) {
        e.preventDefault();
        showToast('Validation Error', 'Please fill in all required fields.', 'error');
      }
    });

    form.querySelectorAll('[required]').forEach(field => {
      field.addEventListener('input', () => {
        if (field.value.trim()) field.classList.remove('is-invalid');
      });
    });
  });
}

// ── Video Player ──
function initVideoPlayer() {
  const video = document.getElementById('lessonVideo');
  if (!video) return;

  const lessonId = video.dataset.lessonId;

  // Restore saved position
  const saved = localStorage.getItem(`video_pos_${lessonId}`);
  if (saved && parseFloat(saved) > 5) {
    video.currentTime = parseFloat(saved);
    showToast('Resumed', `Continuing from ${formatTime(parseFloat(saved))}`, 'info');
  }

  // Save position on pause/unload
  let saveInterval = setInterval(() => {
    if (!video.paused && video.currentTime > 0) {
      localStorage.setItem(`video_pos_${lessonId}`, video.currentTime);
    }
  }, 5000);

  video.addEventListener('ended', () => {
    localStorage.removeItem(`video_pos_${lessonId}`);
    clearInterval(saveInterval);
    // Auto mark complete
    const btn = document.getElementById('markCompleteBtn');
    if (btn) btn.click();
  });

  window.addEventListener('beforeunload', () => {
    if (video.currentTime > 0) localStorage.setItem(`video_pos_${lessonId}`, video.currentTime);
  });
}

// ── Progress Save ──
function initProgressSave() {
  const markBtn = document.getElementById('markCompleteBtn');
  if (!markBtn) return;

  markBtn.addEventListener('click', async () => {
    const lessonId = markBtn.dataset.lessonId;
    try {
      const res = await fetch(`/enrollments/mark-complete/${lessonId}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' }
      });
      const data = await res.json();
      if (data.success) {
        markBtn.innerHTML = '<i class="bi bi-check-circle-fill me-2"></i>Completed!';
        markBtn.disabled = true;
        markBtn.className = 'btn btn-success w-100 mb-2';

        // Update progress bar
        const bar = document.getElementById('progressBar');
        if (bar) {
          bar.style.width = data.progress + '%';
          bar.textContent = data.progress + '%';
        }

        // Mark lesson in sidebar
        const sideItem = document.querySelector(`.lesson-item[data-lesson-id="${lessonId}"]`);
        if (sideItem) {
          sideItem.classList.add('completed');
          const check = sideItem.querySelector('.lesson-check');
          if (check) check.innerHTML = '<i class="bi bi-check"></i>';
        }

        showToast('🎉 Lesson Complete!', `Progress: ${data.progress}%`, 'success');

        if (data.status === 'completed') {
          setTimeout(() => {
            showToast('🏆 Course Completed!', 'Your certificate is ready!', 'success');
          }, 1500);
        }
      }
    } catch { showToast('Error', 'Could not save progress', 'error'); }
  });
}

// ── Scroll animations ──
function initAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('fade-in');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));

  // Smooth counter animation
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseInt(el.dataset.count);
    const duration = 1500;
    const step = target / (duration / 16);
    let current = 0;
    const timer = setInterval(() => {
      current += step;
      if (current >= target) { el.textContent = target.toLocaleString(); clearInterval(timer); }
      else el.textContent = Math.floor(current).toLocaleString();
    }, 16);
  });
}

// ── Search ──
function initSearch() {
  const searchInput = document.getElementById('navSearchInput');
  let searchTimeout;

  searchInput?.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') {
      const q = searchInput.value.trim();
      if (q) window.location.href = `/courses/?q=${encodeURIComponent(q)}`;
    }
  });

  // Course filter auto-submit
  document.querySelectorAll('.filter-select').forEach(select => {
    select.addEventListener('change', () => {
      const form = select.closest('form');
      if (form) form.submit();
    });
  });
}

// ── Quiz Engine ──
class QuizEngine {
  constructor(quizId, timeLimit) {
    this.quizId = quizId;
    this.timeLimit = timeLimit * 60; // convert to seconds
    this.remaining = this.timeLimit;
    this.answers = {};
    this.startTime = Date.now();
    this.timer = null;

    if (timeLimit > 0) this.startTimer();
    this.bindChoices();
  }

  startTimer() {
    const display = document.getElementById('quizTimer');
    if (!display) return;

    this.timer = setInterval(() => {
      this.remaining--;
      const m = Math.floor(this.remaining / 60);
      const s = this.remaining % 60;
      display.textContent = `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;

      if (this.remaining <= 60) display.classList.add('urgent');
      if (this.remaining <= 0) { clearInterval(this.timer); this.submit(); }
    }, 1000);
  }

  bindChoices() {
    document.querySelectorAll('.choice-option').forEach(opt => {
      opt.addEventListener('click', () => {
        const qId = opt.dataset.questionId;
        const cId = opt.dataset.choiceId;

        // Deselect siblings
        document.querySelectorAll(`.choice-option[data-question-id="${qId}"]`)
          .forEach(o => o.classList.remove('selected'));

        opt.classList.add('selected');
        this.answers[qId] = cId;

        // Update question status
        const qCard = opt.closest('.quiz-question');
        qCard?.classList.add('answered');
      });
    });
  }

  async submit() {
    if (this.timer) clearInterval(this.timer);
    const timeTaken = Math.floor((Date.now() - this.startTime) / 1000);

    const submitBtn = document.getElementById('submitQuizBtn');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Submitting...'; }

    try {
      const res = await fetch(`/quizzes/${this.quizId}/submit/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ answers: this.answers, time_taken: timeTaken })
      });
      const data = await res.json();
      if (data.success) window.location.href = `/quizzes/result/${data.attempt_id}/`;
    } catch { showToast('Error', 'Submission failed. Please try again.', 'error'); }
  }
}

// ── Admin actions ──
async function toggleUserStatus(userId, btn) {
  try {
    const res = await fetch(`/dashboard/toggle-user/${userId}/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' }
    });
    const data = await res.json();
    if (data.success) {
      btn.textContent = data.is_active ? 'Deactivate' : 'Activate';
      btn.className = data.is_active ? 'btn btn-sm btn-outline-danger' : 'btn btn-sm btn-outline-success';
      showToast('Updated', `User ${data.is_active ? 'activated' : 'deactivated'}`, 'success');
    }
  } catch { showToast('Error', 'Action failed', 'error'); }
}

// ── Utilities ──
function getCsrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
    document.cookie.split('; ').find(r => r.startsWith('csrftoken='))?.split('=')[1] || '';
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2,'0')}`;
}

// Rating star input
function initStarRating() {
  document.querySelectorAll('.star-rating-input').forEach(container => {
    const stars = container.querySelectorAll('label');
    stars.forEach(star => {
      star.addEventListener('mouseover', () => {
        const val = star.dataset.value;
        stars.forEach(s => s.classList.toggle('active', s.dataset.value <= val));
      });
    });
  });
}

// Delete confirmation
function confirmDelete(formId, name) {
  if (confirm(`Are you sure you want to delete "${name}"? This cannot be undone.`)) {
    document.getElementById(formId).submit();
  }
}

// Price toggle for course form
document.getElementById('id_price_type')?.addEventListener('change', function() {
  const priceFields = document.getElementById('priceFields');
  if (priceFields) priceFields.style.display = this.value === 'paid' ? 'block' : 'none';
});

// Module accordion in learning page
document.querySelectorAll('.module-header-accordion').forEach(header => {
  header.addEventListener('click', () => {
    const content = header.nextElementSibling;
    const icon = header.querySelector('.accordion-icon');
    if (content) {
      const isOpen = content.style.display !== 'none';
      content.style.display = isOpen ? 'none' : 'block';
      if (icon) icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
    }
  });
});
