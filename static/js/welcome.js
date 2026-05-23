// ── Particle canvas ────────────────────────────────────────
const canvas = document.getElementById('hero-canvas');
const ctx = canvas.getContext('2d');
let particles = [];

function resizeCanvas() {
  canvas.width  = window.innerWidth;
  canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

class Particle {
  constructor() { this.reset(); }
  reset() {
    this.x  = Math.random() * canvas.width;
    this.y  = Math.random() * canvas.height;
    this.vx = (Math.random() - 0.5) * 0.4;
    this.vy = (Math.random() - 0.5) * 0.4;
    this.r  = Math.random() * 1.5 + 0.3;
    this.alpha = Math.random() * 0.5 + 0.1;
    this.color = Math.random() < 0.5 ? '245,166,35' : '91,159,255';
  }
  update() {
    this.x += this.vx; this.y += this.vy;
    if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) this.reset();
  }
  draw() {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${this.color},${this.alpha})`;
    ctx.fill();
  }
}

for (let i = 0; i < 120; i++) particles.push(new Particle());

function drawLines() {
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const dx = particles[i].x - particles[j].x;
      const dy = particles[i].y - particles[j].y;
      const dist = Math.sqrt(dx*dx + dy*dy);
      if (dist < 90) {
        ctx.beginPath();
        ctx.moveTo(particles[i].x, particles[i].y);
        ctx.lineTo(particles[j].x, particles[j].y);
        ctx.strokeStyle = `rgba(245,166,35,${0.06 * (1 - dist/90)})`;
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }
    }
  }
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  particles.forEach(p => { p.update(); p.draw(); });
  drawLines();
  requestAnimationFrame(animateParticles);
}
animateParticles();

// ── Nav scroll ─────────────────────────────────────────────
window.addEventListener('scroll', () => {
  document.getElementById('mainNav').classList.toggle('scrolled', window.scrollY > 40);
});

// ── Scroll reveal ──────────────────────────────────────────
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal, .reveal-left, .reveal-right')
        .forEach(el => observer.observe(el));

// ── Animated counter ───────────────────────────────────────
const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target.querySelector('[data-count]');
    if (!el || el._counted) return;
    el._counted = true;
    const target = parseInt(el.dataset.count);
    let cur = 0;
    const step = () => {
      cur = Math.min(cur + 1, target);
      el.textContent = cur;
      if (cur < target) requestAnimationFrame(step);
    };
    step();
  });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-item').forEach(el => counterObserver.observe(el));

// ── Terminal typewriter ────────────────────────────────────
const lines = [
  { text: '$ cd formal_methods_platform',    cls: 'prompt', delay: 400 },
  { text: '$ pip install -r requirements.txt', cls: 'prompt', delay: 900 },
  { text: 'Collecting Flask...', cls: 'out', delay: 1400 },
  { text: 'Successfully installed Flask-3.1.3', cls: 'ok', delay: 1800 },
  { text: '$ python app.py', cls: 'prompt', delay: 2400 },
  { text: ' * Running on http://127.0.0.1:5000', cls: 'blue', delay: 2900 },
  { text: ' * Debug mode: on', cls: 'out', delay: 3100 },
  { text: '127.0.0.1 - GET /automata → 200', cls: 'ok', delay: 3700 },
  { text: '127.0.0.1 - POST /api/resolution/solve → 200', cls: 'ok', delay: 4100 },
  { text: '127.0.0.1 - POST /api/unification/solve → 200', cls: 'ok', delay: 4500 },
];

const termBody = document.getElementById('terminal-body');
const termObserver = new IntersectionObserver((entries) => {
  if (!entries[0].isIntersecting || termBody._started) return;
  termBody._started = true;

  lines.forEach(({ text, cls, delay }) => {
    setTimeout(() => {
      const div = document.createElement('div');
      const clsMap = { prompt:'t-prompt', out:'t-out', ok:'t-ok', blue:'t-blue', purple:'t-purple' };

      if (cls === 'prompt') {
        const [dollar, ...rest] = text.split(' ');
        div.innerHTML = `<span class="t-prompt">$</span> <span class="t-cmd">${rest.join(' ')}</span>`;
      } else {
        div.innerHTML = `<span class="${clsMap[cls] || 't-out'}">${text}</span>`;
      }
      termBody.appendChild(div);
      termBody.scrollTop = termBody.scrollHeight;
    }, delay);
  });

  // cursor at end
  setTimeout(() => {
    const cur = document.createElement('div');
    cur.innerHTML = '<span class="t-prompt">$</span> <span class="t-cursor"></span>';
    termBody.appendChild(cur);
  }, 5000);
}, { threshold: 0.3 });

termObserver.observe(termBody);

// ── Smooth anchor scroll ───────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    document.querySelector(a.getAttribute('href'))?.scrollIntoView({ behavior: 'smooth' });
  });
});