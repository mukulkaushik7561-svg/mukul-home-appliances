const menuButton = document.querySelector('.menu-toggle');
const nav = document.querySelector('.nav');
const progress = document.querySelector('.scroll-progress span');

menuButton?.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  menuButton.setAttribute('aria-expanded', String(open));
  menuButton.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
});

document.querySelectorAll('.nav a').forEach((link) => link.addEventListener('click', () => {
  nav.classList.remove('open');
  menuButton?.setAttribute('aria-expanded', 'false');
}));

window.addEventListener('scroll', () => {
  const available = document.documentElement.scrollHeight - window.innerHeight;
  const amount = available > 0 ? (window.scrollY / available) * 100 : 0;
  progress.style.width = `${amount}%`;
}, { passive: true });

if ('IntersectionObserver' in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));
} else {
  document.querySelectorAll('.reveal').forEach((element) => element.classList.add('visible'));
}

const form = document.querySelector('#enquiryForm');
const status = document.querySelector('#formStatus');

document.querySelectorAll('.enquiry-preset').forEach((button) => {
  button.addEventListener('click', () => {
    const select = form?.elements.service;
    if (select) select.value = button.dataset.service || '';
    document.querySelector('#enquiry')?.scrollIntoView({ behavior: 'smooth' });
    window.setTimeout(() => select?.focus(), 550);
  });
});

form?.addEventListener('submit', async (event) => {
  event.preventDefault();
  form.querySelectorAll('.invalid').forEach((field) => field.classList.remove('invalid'));
  if (!form.checkValidity()) {
    const firstInvalid = form.querySelector(':invalid');
    firstInvalid?.classList.add('invalid');
    firstInvalid?.focus();
    status.className = 'form-status error';
    status.textContent = 'Please complete all fields correctly.';
    return;
  }

  form.classList.add('busy');
  status.className = 'form-status';
  status.textContent = 'Sending your enquiry…';
  try {
    const response = await fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' },
      credentials: 'same-origin',
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'Unable to send your enquiry.');
    form.reset();
    status.className = 'form-status success';
    status.textContent = data.message;
  } catch (error) {
    status.className = 'form-status error';
    status.textContent = `${error.message || 'Something went wrong.'} You can also call +91 9466667561.`;
  } finally {
    form.classList.remove('busy');
  }
});
