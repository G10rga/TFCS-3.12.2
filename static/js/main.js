/* ══════════════════════════════════════════════════════
   FormalCS Platform — Main JavaScript
   UI utilities: sidebar, tabs, accordions, toasts, API
   ══════════════════════════════════════════════════════ */

// ── Sidebar Toggle ─────────────────────────────────────
const sidebar = document.getElementById('sidebar');
const mobileToggle = document.getElementById('mobileToggle');
const sidebarBackdrop = document.getElementById('sidebarBackdrop');

function setSidebarOpen(open) {
    if (!sidebar) return;
    sidebar.classList.toggle('open', open);
    sidebarBackdrop?.classList.toggle('visible', open);
    document.body.classList.toggle('sidebar-open', open);
    if (mobileToggle) {
        mobileToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    }
}

function closeSidebar() {
    setSidebarOpen(false);
}

if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        setSidebarOpen(!sidebar.classList.contains('open'));
    });

    sidebarBackdrop?.addEventListener('click', closeSidebar);

    sidebar.querySelectorAll('.nav-item').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 900) closeSidebar();
        });
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 900) closeSidebar();
    });
}

// ── Tabs ───────────────────────────────────────────────
document.querySelectorAll('.tabs').forEach(tabGroup => {
    tabGroup.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const target = btn.dataset.tab;
            const container = tabGroup.closest('[data-tabs]') || document;

            tabGroup.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            container.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            container.querySelector(`#${target}`)?.classList.add('active');
        });
    });
});

// ── Accordions ─────────────────────────────────────────
document.querySelectorAll('.accordion-header').forEach(header => {
    header.addEventListener('click', () => {
        const item = header.closest('.accordion-item');
        item.classList.toggle('open');
    });
});

// ── Toast Notifications ────────────────────────────────
window.showToast = function(message, type = 'info', duration = 3500) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = {
        success: '✓',
        error: '✗',
        info: 'ℹ',
        warning: '⚠'
    };

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span style="color: ${type === 'success' ? 'var(--green)' : type === 'error' ? 'var(--red)' : 'var(--accent)'}; font-size: 14px; flex-shrink:0">${icons[type] || '•'}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'none';
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(8px)';
        toast.style.transition = '0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
};

// ── Loading State Helpers ──────────────────────────────
window.setLoading = function(btn, loading) {
    if (!btn) return;
    if (loading) {
        btn._originalContent = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = `<span class="loading-spinner"></span> Processing...`;
    } else {
        btn.disabled = false;
        if (btn._originalContent) btn.innerHTML = btn._originalContent;
    }
};

// ── API Helper ─────────────────────────────────────────
window.apiCall = async function(endpoint, data, btn = null) {
    setLoading(btn, true);
    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const json = await res.json();
        return json;
    } catch (e) {
        showToast('Network error: ' + e.message, 'error');
        return null;
    } finally {
        setLoading(btn, false);
    }
};

// ── Copy to Clipboard ──────────────────────────────────
window.copyText = function(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success', 2000);
    }).catch(() => {
        showToast('Copy failed', 'error');
    });
};

// ── Format Clause Display ──────────────────────────────
window.formatLiteral = function(lit) {
    if (lit.startsWith('~')) return `¬${lit.slice(1)}`;
    return lit;
};

window.formatClause = function(lits) {
    if (!lits || lits.length === 0) return '□ (empty)';
    return lits.map(formatLiteral).join(' ∨ ');
};

// ── Highlight formula symbols ──────────────────────────
window.highlightFormula = function(formula) {
    return formula
        .replace(/¬/g, '<span style="color:var(--red)">¬</span>')
        .replace(/∧/g, '<span style="color:var(--blue)">∧</span>')
        .replace(/∨/g, '<span style="color:var(--green)">∨</span>')
        .replace(/→/g, '<span style="color:var(--accent)">→</span>')
        .replace(/↔/g, '<span style="color:var(--purple)">↔</span>')
        .replace(/([A-Z][a-z0-9_]*|[a-z][a-z0-9_]*)/g, '<span style="color:var(--text-primary)">$1</span>');
};

// ── Auto-init animations on cards ─────────────────────
document.querySelectorAll('.card').forEach((card, i) => {
    card.style.animationDelay = `${i * 40}ms`;
    card.classList.add('card-animate');
});

// ── Keyboard shortcut: Ctrl+Enter to submit ────────────
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const btn = document.querySelector('.btn-primary[data-primary]');
        if (btn && !btn.disabled) btn.click();
    }
});