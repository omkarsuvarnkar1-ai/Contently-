/**
 * Contently — Clickable Frontend Prototype
 * Core Application Engine & Demo Utilities (shared/demo-app.js)
 */

(function () {
  'use strict';

  // Helper to find elements by text safely without invalid CSS selectors
  function findElementsByText(selector, text) {
    const elements = document.querySelectorAll(selector);
    const matched = [];
    const lower = text.toLowerCase();
    for (const el of elements) {
      if (el.textContent && el.textContent.toLowerCase().includes(lower)) {
        matched.push(el);
      }
    }
    return matched;
  }

  // -------------------------------------------------------------------------
  // 1. ROUTE DEFINITIONS & RESOLUTION
  // -------------------------------------------------------------------------
  const ROUTES = {
    'landing': { clean: '/', file: '../landing/code.html', public: true },
    'login': { clean: '/login', file: '../login/code.html', public: true },
    'signup': { clean: '/signup', file: '../signup/code.html', public: true },
    'dashboard': { clean: '/dashboard', file: '../dashboard/code.html', public: false },
    'ai-studio': { clean: '/ai-studio', file: '../studio/code.html', public: false },
    'studio': { clean: '/ai-studio', file: '../studio/code.html', public: false },
    'content-editor': { clean: '/content-editor', file: '../editor/code.html', public: false },
    'editor': { clean: '/content-editor', file: '../editor/code.html', public: false },
    'content-library': { clean: '/content-library', file: '../library/code.html', public: false },
    'library': { clean: '/content-library', file: '../library/code.html', public: false },
    'content-planner': { clean: '/content-planner', file: '../planner/code.html', public: false },
    'content-repurposing': { clean: '/content-repurposing', file: '../repurposing/code.html', public: false },
    'repurposing': { clean: '/content-repurposing', file: '../repurposing/code.html', public: false },
    'templates': { clean: '/templates', file: '../templates/code.html', public: false },
    'seo-assistant': { clean: '/seo-assistant', file: '../seo/code.html', public: false },
    'seo': { clean: '/seo-assistant', file: '../seo/code.html', public: false },
    'brand-kit': { clean: '/brand-kit', file: '../brand-kit/code.html', public: false },
    'profile-settings': { clean: '/profile-settings', file: '../settings/code.html', public: false },
    'settings': { clean: '/profile-settings', file: '../settings/code.html', public: false },
    'profile': { clean: '/profile-settings', file: '../settings/code.html', public: false },
    'planner': { clean: '/content-planner', file: '../planner/code.html', public: false },
    '404': { clean: '/404', file: '../404/code.html', public: true }
  };

  function isCleanUrlMode() {
    const path = window.location.pathname;
    return !path.includes('code.html') && !path.includes('.html');
  }

  function resolveUrl(routeKey) {
    const route = ROUTES[routeKey] || ROUTES['dashboard'];
    if (isCleanUrlMode()) {
      return route.clean;
    }
    if (window.location.pathname === '/' || window.location.pathname.endsWith('/index.html')) {
      return route.file.replace(/^\.\.\//, './');
    }
    return route.file;
  }

  function navigateTo(routeKey) {
    window.location.href = resolveUrl(routeKey);
  }

  function getCurrentRouteKey() {
    const p = window.location.pathname.toLowerCase();
    for (const [key, val] of Object.entries(ROUTES)) {
      if (p === val.clean || p.endsWith(val.clean)) return key;
      const folderName = val.file.split('/')[1];
      if (p.includes(folderName)) return key;
    }
    if (p.includes('dashboard')) return 'dashboard';
    if (p.includes('login')) return 'login';
    if (p.includes('sign_up') || p.includes('signup')) return 'signup';
    if (p.includes('landing')) return 'landing';
    if (p.includes('editor')) return 'content-editor';
    if (p.includes('library')) return 'content-library';
    if (p.includes('planner')) return 'content-planner';
    if (p.includes('repurpos')) return 'content-repurposing';
    if (p.includes('studio')) return 'ai-studio';
    if (p.includes('template')) return 'templates';
    if (p.includes('brand')) return 'brand-kit';
    if (p.includes('seo')) return 'seo-assistant';
    if (p.includes('profile') || p.includes('setting')) return 'profile-settings';
    return 'landing';
  }

  // -------------------------------------------------------------------------
  // 2. DEMO AUTHENTICATION SERVICE
  // -------------------------------------------------------------------------
  const DEFAULT_DEMO_USER = {
    name: 'Omkar Sharma',
    email: 'demo@contently.local',
    password: 'ContentlyDemo123!',
    role: 'Pro Creator',
    avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDJ9-i1Rr_McZcEqHc300dlnvuSl4X_Jr1rT14gwFcUXtv77NmEtv6OO15aZDoL77BbQt8I0v6Gwm8gjSzG2mxICW1gndG6NwIaZk4ydrYnQqO4TYzUfv3OpPvhd6q5CSiTp_f1L9KFMsZCMXcQ8XiwS815pzIOaNc-69wDKmVt4Yz8Gg5uZ2cFsnBljp66brow6kVCYb64xr8tZZsprLOgT4x0Z6q5CPuKpgVUvuc'
  };

  const ContentlyAuth = {
    getStoredUser() {
      try {
        const raw = localStorage.getItem('contently_demo_user');
        return raw ? JSON.parse(raw) : null;
      } catch (e) {
        return null;
      }
    },
    isLoggedIn() {
      return !!this.getStoredUser();
    },
    async login(email, password) {
      email = (email || '').trim().toLowerCase();
      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (res.ok && data.token) {
          localStorage.setItem('contently_token', data.token);
          localStorage.setItem('contently_demo_user', JSON.stringify(data.user));
          return { success: true, user: data.user };
        }
        return { success: false, message: data.detail || 'Invalid email or password.' };
      } catch (err) {
        // Graceful fallback for standalone preview
        if (email === DEFAULT_DEMO_USER.email.toLowerCase() && password === DEFAULT_DEMO_USER.password) {
          localStorage.setItem('contently_demo_user', JSON.stringify(DEFAULT_DEMO_USER));
          return { success: true, user: DEFAULT_DEMO_USER };
        }
        if (email && email.includes('@') && password && password.length >= 6) {
          const mockUser = {
            name: email.split('@')[0],
            email: email,
            role: 'Pro Creator',
            avatar: DEFAULT_DEMO_USER.avatar
          };
          localStorage.setItem('contently_demo_user', JSON.stringify(mockUser));
          return { success: true, user: mockUser };
        }
        return { success: false, message: 'Server unreachable and invalid credentials.' };
      }
    },
    async signup(name, email, password) {
      email = (email || '').trim().toLowerCase();
      name = (name || '').trim() || 'Creator';
      if (!name || !email || !password) {
        return { success: false, message: 'Please fill in all required fields.' };
      }
      if (!email.includes('@')) {
        return { success: false, message: 'Please enter a valid email address.' };
      }
      if (password.length < 8) {
        return { success: false, message: 'Password must be at least 8 characters long.' };
      }
      try {
        const res = await fetch('/api/auth/signup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ full_name: name, email: email, password: password })
        });
        const data = await res.json();
        if (res.ok && data.token) {
          localStorage.setItem('contently_token', data.token);
          localStorage.setItem('contently_demo_user', JSON.stringify(data.user));
          return { success: true, user: data.user };
        }
        return { success: false, message: data.detail || 'Signup failed. Please try again.' };
      } catch (err) {
        const newUser = {
          name,
          email,
          role: 'Pro Creator',
          avatar: DEFAULT_DEMO_USER.avatar
        };
        localStorage.setItem('contently_demo_user', JSON.stringify(newUser));
        return { success: true, user: newUser };
      }
    },
    async oauthLogin(provider, email, name, avatarUrl, providerId) {
      try {
        const res = await fetch('/api/auth/oauth', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider,
            email,
            name,
            avatar_url: avatarUrl,
            provider_id: providerId || `${provider}_${Date.now()}`
          })
        });
        const data = await res.json();
        if (res.ok && data.token) {
          localStorage.setItem('contently_token', data.token);
          localStorage.setItem('contently_demo_user', JSON.stringify(data.user));
          return { success: true, user: data.user, isNew: data.is_new };
        }
        return { success: false, message: data.detail || 'OAuth authentication failed.' };
      } catch (err) {
        const mockUser = {
          name: name || 'Creator',
          email: email,
          role: 'Pro Creator',
          avatar: avatarUrl || DEFAULT_DEMO_USER.avatar,
          oauth_provider: provider
        };
        localStorage.setItem('contently_demo_user', JSON.stringify(mockUser));
        return { success: true, user: mockUser, isNew: true };
      }
    },
    async getProviders() {
      try {
        const res = await fetch('/api/auth/providers');
        if (res.ok) return await res.json();
      } catch (e) {}
      return {
        google: { enabled: false },
        github: { enabled: false }
      };
    },
    openOAuthModal(provider = 'google', isSignup = false) {
      let modal = document.getElementById('contently-oauth-modal');
      if (modal) modal.remove();

      modal = document.createElement('div');
      modal.id = 'contently-oauth-modal';
      modal.className = 'contently-modal-overlay active';

      const isGoogle = provider === 'google';
      const brandName = isGoogle ? 'Google' : 'GitHub';
      const actionText = isSignup ? 'Sign up' : 'Sign in';

      const googleSvg = `<svg class="w-6 h-6" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"></path><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"></path><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"></path><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"></path></svg>`;

      const githubSvg = `<svg class="w-6 h-6 fill-current text-white" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"></path></svg>`;

      modal.innerHTML = `
        <div class="contently-modal-card oauth-card">
          <div id="oauth-loading-bar" class="oauth-progress-bar" style="display: none;">
            <div class="oauth-progress-indeterminate ${isGoogle ? 'google' : 'github'}"></div>
          </div>
          <div class="oauth-brand-header">
            <button id="close-oauth-modal" class="absolute top-4 right-4 text-outline hover:text-on-surface p-1 rounded-lg">
              <span class="material-symbols-outlined text-lg">close</span>
            </button>
            <div class="oauth-brand-badge ${isGoogle ? 'google' : 'github'}">
              ${isGoogle ? googleSvg : githubSvg}
            </div>
            <h3 class="font-headline-sm text-lg font-bold text-on-surface">${actionText} with ${brandName}</h3>
            <p class="font-body-sm text-xs text-on-surface-variant mt-0.5">to continue to <strong>Contently AI Platform</strong></p>
          </div>

          <div class="p-6 flex flex-col gap-3">
            <p class="text-xs font-semibold text-outline uppercase tracking-wider mb-1">Choose an account</p>

            ${isGoogle ? `
              <!-- Google Account 1 -->
              <button class="oauth-account-item select-oauth-btn" data-email="omkar.creator@gmail.com" data-name="Omkar Sharma" data-avatar="https://lh3.googleusercontent.com/aida-public/AB6AXuDJ9-i1Rr_McZcEqHc300dlnvuSl4X_Jr1rT14gwFcUXtv77NmEtv6OO15aZDoL77BbQt8I0v6Gwm8gjSzG2mxICW1gndG6NwIaZk4ydrYnQqO4TYzUfv3OpPvhd6q5CSiTp_f1L9KFMsZCMXcQ8XiwS815pzIOaNc-69wDKmVt4Yz8Gg5uZ2cFsnBljp66brow6kVCYb64xr8tZZsprLOgT4x0Z6q5CPuKpgVUvuc" type="button">
                <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuDJ9-i1Rr_McZcEqHc300dlnvuSl4X_Jr1rT14gwFcUXtv77NmEtv6OO15aZDoL77BbQt8I0v6Gwm8gjSzG2mxICW1gndG6NwIaZk4ydrYnQqO4TYzUfv3OpPvhd6q5CSiTp_f1L9KFMsZCMXcQ8XiwS815pzIOaNc-69wDKmVt4Yz8Gg5uZ2cFsnBljp66brow6kVCYb64xr8tZZsprLOgT4x0Z6q5CPuKpgVUvuc" class="w-10 h-10 rounded-full object-cover ring-2 ring-primary/20" alt="Avatar"/>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-bold text-on-surface truncate">Omkar Sharma</p>
                  <p class="text-xs text-on-surface-variant truncate">omkar.creator@gmail.com</p>
                </div>
                <span class="material-symbols-outlined text-outline text-base">chevron_right</span>
              </button>

              <!-- Google Account 2 -->
              <button class="oauth-account-item select-oauth-btn" data-email="creator.studio@gmail.com" data-name="Creative Studio" data-avatar="https://lh3.googleusercontent.com/aida-public/AB6AXuBLVXDm-AY3rlwq0oifcdvDzcmbFrjnpogTdelvdes_E9Ny_-9YNZjA-PYgKcarDxzuah2pwaq8TYBpeAtrcaJ4v1j6UR-ECchIOw-J6DPvsAAb98uVl0xINzEelI7sLM0bffpcuN8t5EmqiFC59omoZD6kSpLxktVRnD6dUU3YTBv1SDgEoiiLu4ckSyvcgI8eCNsHATwO89-zd9EQdX2iN0P9_6gAEv7BUPrSi_g" type="button">
                <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuBLVXDm-AY3rlwq0oifcdvDzcmbFrjnpogTdelvdes_E9Ny_-9YNZjA-PYgKcarDxzuah2pwaq8TYBpeAtrcaJ4v1j6UR-ECchIOw-J6DPvsAAb98uVl0xINzEelI7sLM0bffpcuN8t5EmqiFC59omoZD6kSpLxktVRnD6dUU3YTBv1SDgEoiiLu4ckSyvcgI8eCNsHATwO89-zd9EQdX2iN0P9_6gAEv7BUPrSi_g" class="w-10 h-10 rounded-full object-cover ring-2 ring-secondary/20" alt="Avatar"/>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-bold text-on-surface truncate">Creative Studio</p>
                  <p class="text-xs text-on-surface-variant truncate">creator.studio@gmail.com</p>
                </div>
                <span class="material-symbols-outlined text-outline text-base">chevron_right</span>
              </button>
            ` : `
              <!-- GitHub Account 1 -->
              <button class="oauth-account-item select-oauth-btn" data-email="omkar.dev@github.com" data-name="omkar-builds" data-avatar="https://lh3.googleusercontent.com/aida-public/AB6AXuCndEEYVdQMGsaKubGEYSLL5VPSIhWpNkH0CqtO93II5KGng9hXyem-kAtowvzF0Lks8XPtWolWmuBmccP1p8bv7xJNY5QQjuDSMfUcZLnCMa7OIfvZ3nURpj-LRiB6kx2r9hyFZFrZzeV9tvUmsZ4BqoFAp08FAv-lX21AlsaGoBDG-0DPe55-X_UrA2vl6dy3Ds3AvCjd4SRUXnXlBiTFtSBGHKoFd5WI8btFvN8" type="button">
                <div class="w-10 h-10 rounded-full bg-slate-900 flex items-center justify-center text-white ring-2 ring-slate-800">
                  <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"></path></svg>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-bold text-on-surface truncate">omkar-builds</p>
                  <p class="text-xs text-on-surface-variant truncate">omkar.dev@github.com</p>
                </div>
                <span class="material-symbols-outlined text-outline text-base">chevron_right</span>
              </button>
            `}

            <!-- Custom Account Toggle -->
            <div class="mt-2 pt-2 border-t border-slate-100">
              <button id="toggle-custom-oauth" type="button" class="w-full text-left py-2 px-1 text-xs font-semibold text-primary hover:text-primary-container flex items-center justify-between">
                <span>Use a different ${brandName} account</span>
                <span class="material-symbols-outlined text-sm">expand_more</span>
              </button>
              <div id="custom-oauth-form" style="display: none;" class="mt-2 space-y-2 p-3 bg-surface-container-low rounded-xl">
                <input id="custom-oauth-name" type="text" placeholder="${isGoogle ? 'Your Full Name' : 'GitHub Username'}" class="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-on-surface bg-white focus:outline-none focus:border-primary"/>
                <input id="custom-oauth-email" type="email" placeholder="name@domain.com" class="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-on-surface bg-white focus:outline-none focus:border-primary"/>
                <button id="submit-custom-oauth" type="button" class="w-full py-2 px-3 rounded-lg bg-primary text-white text-xs font-bold hover:bg-primary-container transition-all shadow-sm">
                  Continue with this Account
                </button>
              </div>
            </div>

            <!-- Official Live OAuth Redirect Button -->
            <div class="mt-2 pt-2 border-t border-slate-100 flex flex-col gap-1.5">
              <button id="direct-oauth-redirect" type="button" class="w-full py-2 px-3 rounded-xl border border-slate-300 hover:bg-slate-50 text-on-surface text-xs font-bold transition-all flex items-center justify-center gap-1.5 shadow-sm">
                <span class="material-symbols-outlined text-sm">open_in_new</span>
                <span>Open Official ${brandName} Sign-In Screen</span>
              </button>
              <p class="text-[10px] text-outline text-center">Requires ${isGoogle ? 'GOOGLE_CLIENT_ID' : 'GITHUB_CLIENT_ID'} in backend/.env</p>
            </div>

            <!-- Notice Footer -->
            <p class="text-[11px] text-outline text-center mt-3 leading-relaxed">
              By continuing, Contently will access your name, email address, and avatar. See our <a href="#" class="underline">Privacy Policy</a>.
            </p>
          </div>
        </div>
      `;

      document.body.appendChild(modal);

      const closeModal = () => {
        modal.classList.remove('active');
        setTimeout(() => modal.remove(), 200);
      };

      modal.querySelector('#close-oauth-modal').addEventListener('click', closeModal);
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
      });

      // Toggle custom form
      const toggleBtn = modal.querySelector('#toggle-custom-oauth');
      const customForm = modal.querySelector('#custom-oauth-form');
      toggleBtn.addEventListener('click', () => {
        const isHidden = customForm.style.display === 'none';
        customForm.style.display = isHidden ? 'block' : 'none';
        toggleBtn.querySelector('.material-symbols-outlined').textContent = isHidden ? 'expand_less' : 'expand_more';
      });

      const handleOAuthSubmit = async (email, name, avatar) => {
        const loadingBar = modal.querySelector('#oauth-loading-bar');
        if (loadingBar) loadingBar.style.display = 'block';

        showToast(`Authenticating with ${brandName}...`, 'info', 2000);
        const result = await ContentlyAuth.oauthLogin(provider, email, name, avatar);

        if (result.success) {
          closeModal();
          showToast(`${actionText} successful! Welcome to Contently, ${result.user.name || result.user.full_name}!`, 'success', 3500);
          setTimeout(() => {
            navigateTo('dashboard');
          }, 800);
        } else {
          if (loadingBar) loadingBar.style.display = 'none';
          showToast(result.message || 'Authentication failed.', 'error');
        }
      };

      // Select preset accounts
      modal.querySelectorAll('.select-oauth-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const email = btn.getAttribute('data-email');
          const name = btn.getAttribute('data-name');
          const avatar = btn.getAttribute('data-avatar');
          handleOAuthSubmit(email, name, avatar);
        });
      });

      // Submit custom account
      modal.querySelector('#submit-custom-oauth').addEventListener('click', () => {
        const name = modal.querySelector('#custom-oauth-name').value.trim();
        const email = modal.querySelector('#custom-oauth-email').value.trim();
        if (!email || !email.includes('@')) {
          showToast('Please enter a valid email address.', 'warning');
          return;
        }
        const avatar = isGoogle
          ? DEFAULT_DEMO_USER.avatar
          : (name ? `https://github.com/${name}.png` : DEFAULT_DEMO_USER.avatar);
        handleOAuthSubmit(email, name || email.split('@')[0], avatar);
      });

      // Direct official OAuth redirect
      const directBtn = modal.querySelector('#direct-oauth-redirect');
      if (directBtn) {
        directBtn.addEventListener('click', () => {
          window.location.href = isGoogle ? '/api/auth/google/authorize' : '/api/auth/github/authorize';
        });
      }
    },
    async ensureToken() {
      let token = localStorage.getItem('contently_token');
      if (token) return token;
      const user = this.getStoredUser();
      if (!user) return null;
      try {
        const res = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: user.email || 'demo@contently.local',
            password: user.password || 'ContentlyDemo123!'
          })
        });
        const data = await res.json();
        if (data.token) {
          localStorage.setItem('contently_token', data.token);
          return data.token;
        }
      } catch (e) {
        // Fallback gracefully
      }
      return null;
    },
    logout() {
      try {
        fetch('/api/auth/logout', { method: 'POST' });
      } catch (e) {}
      localStorage.removeItem('contently_demo_user');
      localStorage.removeItem('contently_token');
      showToast('Logged out of workspace session', 'info');
      setTimeout(() => {
        navigateTo('login');
      }, 500);
    }
  };

  // -------------------------------------------------------------------------
  // 3. TOAST NOTIFICATION UTILITY
  // -------------------------------------------------------------------------
  function ensureToastContainer() {
    let container = document.getElementById('contently-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'contently-toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  function showToast(message, type = 'info', duration = 3600) {
    const container = ensureToastContainer();
    const toast = document.createElement('div');
    toast.className = `contently-toast toast-${type}`;

    let iconName = 'info';
    if (type === 'success') iconName = 'check_circle';
    if (type === 'warning') iconName = 'warning';
    if (type === 'error') iconName = 'error';

    toast.innerHTML = `
      <span class="material-symbols-outlined text-[20px] toast-icon" style="font-variation-settings: 'FILL' 1;">${iconName}</span>
      <span class="flex-1">${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('toast-exit');
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 300);
    }, duration);
  }

  // -------------------------------------------------------------------------
  // 3B. RAZORPAY BILLING & SUBSCRIPTION CLIENT
  // -------------------------------------------------------------------------
  const ContentlyBilling = {
    scriptPromise: null,

    loadRazorpayScript() {
      if (window.Razorpay) return Promise.resolve(true);
      if (this.scriptPromise) return this.scriptPromise;
      this.scriptPromise = new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = 'https://checkout.razorpay.com/v1/checkout.js';
        s.async = true;
        s.onload = () => resolve(true);
        s.onerror = () => reject(new Error('Failed to load Razorpay Checkout SDK'));
        document.head.appendChild(s);
      });
      return this.scriptPromise;
    },

    async startCheckout(planCode = 'pro_monthly', currency = 'INR') {
      if (!ContentlyAuth.isLoggedIn()) {
        showToast('Please sign in before starting subscription checkout.', 'warning');
        setTimeout(() => navigateTo('login'), 800);
        return;
      }

      showToast('Initializing secure Razorpay checkout in Indian Rupees (INR ₹)...', 'info', 2000);
      const token = await ContentlyAuth.ensureToken();

      try {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = 'Bearer ' + token;

        const res = await fetch('/api/billing/checkout', {
          method: 'POST',
          headers: headers,
          body: JSON.stringify({ plan_code: planCode, currency: currency })
        });

        const data = await res.json();
        if (!res.ok) {
          showToast(data.detail || 'Unable to start checkout. Please check server credentials.', 'error', 4500);
          return;
        }

        await this.loadRazorpayScript();

        const options = {
          key: data.key_id,
          subscription_id: data.subscription_id || undefined,
          order_id: data.order_id || undefined,
          amount: data.amount,
          currency: data.currency || 'INR',
          name: 'Contently',
          description: (data.plan_name || 'Pro Creator Tier') + ' - ' + (data.currency === 'INR' ? (data.billing_interval === 'yearly' ? '₹38,390/yr' : '₹3,999/mo') : '$49/mo'),
          image: 'https://lh3.googleusercontent.com/aida-public/AB6AXuDJ9-i1Rr_McZcEqHc300dlnvuSl4X_Jr1rT14gwFcUXtv77NmEtv6OO15aZDoL77BbQt8I0v6Gwm8gjSzG2mxICW1gndG6NwIaZk4ydrYnQqO4TYzUfv3OpPvhd6q5CSiTp_f1L9KFMsZCMXcQ8XiwS815pzIOaNc-69wDKmVt4Yz8Gg5uZ2cFsnBljp66brow6kVCYb64xr8tZZsprLOgT4x0Z6q5CPuKpgVUvuc',
          prefill: data.prefill || {},
          theme: { color: '#3525cd' },
          handler: async (response) => {
            showToast('Verifying payment on Contently server...', 'info', 3000);
            try {
              const verifyRes = await fetch('/api/billing/verify-payment', {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_subscription_id: response.razorpay_subscription_id || data.subscription_id,
                  razorpay_order_id: response.razorpay_order_id || data.order_id,
                  razorpay_signature: response.razorpay_signature,
                  plan_code: data.plan_code
                })
              });
              const verifyData = await verifyRes.json();
              if (verifyRes.ok && verifyData.success) {
                showToast('Payment verified successfully! Pro Creator subscription activated in INR (₹).', 'success', 4500);
                const currentUser = ContentlyAuth.getStoredUser();
                if (currentUser) {
                  currentUser.role = 'Pro Creator';
                  localStorage.setItem('contently_demo_user', JSON.stringify(currentUser));
                }
              } else {
                showToast(verifyData.detail || 'Payment processed. Finalizing subscription via webhook sync.', 'warning', 4000);
              }
            } catch (err) {
              showToast('Payment authorized. Server webhook finalizing sync.', 'info');
            }
          },
          modal: {
            ondismiss: () => {
              showToast('Checkout dismissed.', 'info', 2000);
            }
          }
        };

        const rzp = new window.Razorpay(options);
        rzp.on('payment.failed', (resp) => {
          showToast('Payment failed: ' + (resp.error?.description || 'Declined'), 'error', 4000);
        });
        rzp.open();
      } catch (err) {
        showToast('Error launching checkout: ' + (err.message || 'Network error'), 'error');
      }
    },

    openSubscriptionPlansModal() {
      const existing = document.getElementById('contently-subscription-modal');
      if (existing) existing.remove();

      const modal = document.createElement('div');
      modal.id = 'contently-subscription-modal';
      modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm';
      modal.innerHTML = `
        <div class="relative w-full max-w-4xl bg-surface-container-lowest rounded-2xl border border-outline-variant/40 shadow-2xl overflow-hidden p-6 md:p-8 space-y-6">
          <div class="flex items-start justify-between">
            <div class="space-y-1">
              <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-primary/10 text-primary border border-primary/20">
                <span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>Active Currency: Indian Rupee (INR ₹)</span>
              </div>
              <h2 class="text-2xl md:text-3xl font-extrabold text-on-surface tracking-tight">Choose Your Subscription Plan</h2>
              <p class="text-sm text-on-surface-variant">All subscriptions are billed securely in Indian Rupees (₹ INR) via Razorpay. Seamless UPI, Cards & Netbanking.</p>
            </div>
            <button id="close-sub-modal-btn" class="p-2 rounded-xl text-outline hover:text-on-surface hover:bg-surface-container-high transition-colors cursor-pointer" title="Close">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"></path></svg>
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
            <!-- Monthly Plan -->
            <div class="rounded-2xl border border-outline-variant/50 p-6 flex flex-col justify-between hover:border-primary/50 transition-all hover:shadow-md bg-surface-container-low/40">
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold uppercase tracking-wider text-primary">Monthly Billing</span>
                  <span class="text-xs px-2.5 py-0.5 rounded-full bg-surface-container text-on-surface-variant font-medium">Cancel Anytime</span>
                </div>
                <div>
                  <h3 class="text-xl font-bold text-on-surface">Pro Creator Tier</h3>
                  <p class="text-xs text-on-surface-variant mt-0.5">Full multi-channel generative AI and publishing pipeline</p>
                </div>
                <div class="flex items-baseline gap-1">
                  <span class="text-3xl font-extrabold text-on-surface">₹3,999</span>
                  <span class="text-sm font-medium text-outline">/ month</span>
                </div>
                <div class="space-y-2.5 pt-2 text-xs text-on-surface-variant">
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>Unlimited autonomous AI content generation</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>500,000 monthly inference tokens</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>10 Brand Kit custom voice profiles</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>Multi-channel publishing (LinkedIn, X, Blogs)</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>Full SEO Keyword Analyzer & Scoring</span>
                  </div>
                </div>
              </div>
              <button class="sub-checkout-btn w-full mt-6 py-3 rounded-xl bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-semibold text-sm transition-all flex items-center justify-center gap-2 cursor-pointer shadow-sm" data-plan="pro_monthly">
                <span>Subscribe Monthly (₹3,999)</span>
                <svg class="w-4 h-4 text-outline" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" stroke-linecap="round" stroke-linejoin="round"></path></svg>
              </button>
            </div>

            <!-- Yearly Plan (Featured) -->
            <div class="relative rounded-2xl border-2 border-primary p-6 flex flex-col justify-between hover:shadow-xl transition-all bg-gradient-to-br from-primary/[0.04] via-surface-container-low to-primary/[0.02]">
              <div class="absolute -top-3 right-6 px-3 py-1 rounded-full text-[11px] font-bold bg-primary text-white shadow-sm flex items-center gap-1">
                <svg class="w-3 h-3 fill-current" viewBox="0 0 24 24"><path d="M12 2L14.4 9.6L22 12L14.4 14.4L12 22L9.6 14.4L2 12L9.6 9.6L12 2Z"></path></svg>
                <span>Save 20% · Best Value</span>
              </div>
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <span class="text-xs font-bold uppercase tracking-wider text-primary">Annual Billing</span>
                  <span class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-700 font-bold">2 Months Free</span>
                </div>
                <div>
                  <h3 class="text-xl font-bold text-on-surface">Pro Creator Tier (Annual)</h3>
                  <p class="text-xs text-on-surface-variant mt-0.5">Year-round full platform access with priority queueing</p>
                </div>
                <div class="space-y-0.5">
                  <div class="flex items-baseline gap-1.5">
                    <span class="text-3xl font-extrabold text-on-surface">₹38,390</span>
                    <span class="text-sm font-medium text-outline">/ year</span>
                  </div>
                  <div class="text-xs font-semibold text-emerald-600">
                    Just ₹3,199/month (Save ₹9,598 compared to monthly)
                  </div>
                </div>
                <div class="space-y-2.5 pt-2 text-xs text-on-surface-variant">
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span><strong>All Pro Creator monthly features included</strong></span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>Priority autonomous agent inference processing</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>Dedicated creator onboarding & workflow setup</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>Unlimited revision drafts & campaign history</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-emerald-600 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round"></path></svg>
                    <span>Instant activation via Razorpay</span>
                  </div>
                </div>
              </div>
              <button class="sub-checkout-btn w-full mt-6 py-3 rounded-xl bg-gradient-to-r from-primary to-primary-container text-white font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer" data-plan="pro_yearly">
                <span>Subscribe Annually (₹38,390)</span>
                <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" stroke-linecap="round" stroke-linejoin="round"></path></svg>
              </button>
            </div>
          </div>

          <div class="pt-2 border-t border-outline-variant/30 flex flex-wrap items-center justify-between text-xs text-on-surface-variant gap-3">
            <div class="flex items-center gap-2">
              <svg class="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" stroke-linecap="round" stroke-linejoin="round"></path></svg>
              <span>Secured by 256-bit Razorpay Encryption</span>
            </div>
            <div class="flex items-center gap-2 font-medium">
              <span class="px-2 py-0.5 rounded bg-surface-container text-on-surface">UPI (GPay / PhonePe / Paytm)</span>
              <span class="px-2 py-0.5 rounded bg-surface-container text-on-surface">Credit / Debit Cards</span>
              <span class="px-2 py-0.5 rounded bg-surface-container text-on-surface">Netbanking</span>
            </div>
          </div>
        </div>
      `;

      document.body.appendChild(modal);

      const closeBtn = modal.querySelector('#close-sub-modal-btn');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => modal.remove());
      }
      modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
      });

      modal.querySelectorAll('.sub-checkout-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const plan = btn.getAttribute('data-plan') || 'pro_monthly';
          modal.remove();
          this.startCheckout(plan, 'INR');
        });
      });
    },

    async cancelSubscription() {
      const token = await ContentlyAuth.ensureToken();
      try {
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = 'Bearer ' + token;

        const res = await fetch('/api/billing/cancel', {
          method: 'POST',
          headers: headers
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast(data.message || 'Subscription cancelled successfully.', 'success');
        } else {
          showToast(data.detail || 'Unable to cancel subscription.', 'error');
        }
      } catch (err) {
        showToast('Cancellation request failed.', 'error');
      }
    },

    async getSubscription() {
      const token = await ContentlyAuth.ensureToken();
      try {
        const headers = {};
        if (token) headers['Authorization'] = 'Bearer ' + token;
        const res = await fetch('/api/billing/subscription', { headers });
        return await res.json();
      } catch (e) {
        return null;
      }
    }
  };

  // -------------------------------------------------------------------------
  // 4. FLOATING DEMO MODE INDICATOR & AUTH BADGE
  // -------------------------------------------------------------------------
  function renderDemoIndicator() {
    if (document.getElementById('contently-demo-indicator')) return;

    const user = ContentlyAuth.getStoredUser();
    const indicator = document.createElement('div');
    indicator.id = 'contently-demo-indicator';

    if (user) {
      indicator.innerHTML = `
        <span class="demo-dot"></span>
        <span>Demo: <strong>${user.email}</strong></span>
        <span style="opacity: 0.35;">|</span>
        <button id="demo-indicator-logout" style="color: #acedff; background: none; border: none; font-size: inherit; font-weight: 700; cursor: pointer; text-decoration: underline; padding: 0;">Logout</button>
        <span style="opacity: 0.35;">|</span>
        <a href="${resolveUrl('landing')}" style="color: #ffffff; text-decoration: none; opacity: 0.85;">Landing</a>
      `;
    } else {
      indicator.innerHTML = `
        <span class="demo-dot" style="background: #fbbf24; box-shadow: 0 0 8px #fbbf24;"></span>
        <span>Demo Prototype</span>
        <span style="opacity: 0.35;">|</span>
        <a href="${resolveUrl('login')}" style="color: #acedff; text-decoration: underline; font-weight: 700;">Sign In</a>
      `;
    }

    document.body.appendChild(indicator);

    const logoutBtn = document.getElementById('demo-indicator-logout');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', (e) => {
        e.preventDefault();
        ContentlyAuth.logout();
      });
    }
  }

  // -------------------------------------------------------------------------
  // 5. SIDEBAR & NAVIGATION WIRING
  // -------------------------------------------------------------------------
  function wireNavigation() {
    const currentKey = getCurrentRouteKey();

    // Wire up sidebar links with data-path
    const sidebarLinks = document.querySelectorAll('aside nav a[data-path]');
    sidebarLinks.forEach(link => {
      const path = link.getAttribute('data-path');
      link.href = resolveUrl(path);

      // Match active path
      const isCurrent = (path === currentKey) ||
        (path === 'profile-settings' && (currentKey === 'profile' || currentKey === 'settings')) ||
        (path === 'content-planner' && currentKey === 'planner');

      if (isCurrent) {
        link.classList.add('bg-primary-container', 'text-on-primary-container', 'font-bold', 'shadow-sm');
        link.classList.remove('text-on-surface-variant');
        link.setAttribute('aria-current', 'page');
      } else {
        link.classList.remove('bg-primary-container', 'text-on-primary-container', 'font-bold', 'shadow-sm');
        link.removeAttribute('aria-current');
      }

      link.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo(path);
      });
    });

    // Wire up Contently brand logo in sidebar and header
    const brandElements = document.querySelectorAll('aside .h-16, header a');
    brandElements.forEach(el => {
      if (el.textContent && el.textContent.includes('Contently')) {
        el.style.cursor = 'pointer';
        el.addEventListener('click', (e) => {
          if (currentKey === 'landing') {
            window.scrollTo({ top: 0, behavior: 'smooth' });
          } else {
            navigateTo('dashboard');
          }
        });
      }
    });

    // Wire up landing page navigation
    if (currentKey === 'landing') {
      const loginLinks = document.querySelectorAll('a[data-target="Login"]');
      loginLinks.forEach(link => {
        link.href = resolveUrl('login');
        link.addEventListener('click', (e) => {
          e.preventDefault();
          navigateTo('login');
        });
      });

      const startButtons = document.querySelectorAll('a[data-target="Start Creating"], a[data-target="Start Creating CTA"], #hero-start-cta');
      startButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          if (ContentlyAuth.isLoggedIn()) {
            navigateTo('ai-studio');
          } else {
            navigateTo('signup');
          }
        });
      });

      // Wire pricing links to open Indian Rupee subscription plans modal
      const pricingLinks = document.querySelectorAll('a[data-target="Pricing"], a[href="#pricing-section"]');
      const textPricing = findElementsByText('a', 'Pricing');
      new Set([...pricingLinks, ...textPricing]).forEach(link => {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          ContentlyBilling.openSubscriptionPlansModal();
        });
      });
    }

    // Wire up "Back to Content Library" or back buttons
    const backToLibraryLinks = findElementsByText('a', 'Back to Content Library');
    backToLibraryLinks.forEach(el => {
      el.href = resolveUrl('content-library');
      el.addEventListener('click', (e) => {
        e.preventDefault();
        navigateTo('content-library');
      });
    });
  }

  // -------------------------------------------------------------------------
  // 6. TOP HEADER QUICK ACTIONS & MODALS
  // -------------------------------------------------------------------------
  function setupHeaderInteractions() {
    // Quick Action Modal for "Create" button
    const createButtons = document.querySelectorAll('header button.interactive-ai-trigger');
    const additionalCreateBtns = findElementsByText('header button', 'Create');
    const allCreateButtons = new Set([...createButtons, ...additionalCreateBtns]);

    allCreateButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        openQuickCreateModal();
      });
    });

    // Notifications Bell Popover
    const notifButtons = findElementsByText('header button', 'notifications');
    notifButtons.forEach(btn => {
      btn.style.position = 'relative';
      let popover = btn.querySelector('.contently-popover');
      if (!popover) {
        popover = document.createElement('div');
        popover.className = 'contently-popover w-80 text-left';
        popover.innerHTML = `
          <div class="flex items-center justify-between pb-2 border-b border-surface-container mb-2">
            <span class="font-bold text-xs text-on-surface uppercase tracking-wider">Workspace Activity</span>
            <span class="text-[11px] text-primary font-semibold">3 New</span>
          </div>
          <div class="flex flex-col gap-2 text-xs">
            <div class="p-2 rounded-lg bg-surface-container-low flex items-start gap-2">
              <span class="material-symbols-outlined text-primary text-base">auto_awesome</span>
              <div>
                <p class="font-bold text-on-surface">Voice Model v4.2 Active</p>
                <p class="text-on-surface-variant text-[11px]">Calibrated at 98% brand resonance.</p>
              </div>
            </div>
            <div class="p-2 rounded-lg bg-surface-container-low flex items-start gap-2">
              <span class="material-symbols-outlined text-secondary text-base">schedule</span>
              <div>
                <p class="font-bold text-on-surface">LinkedIn Post Queued</p>
                <p class="text-on-surface-variant text-[11px]">Scheduled for tomorrow, 9:00 AM.</p>
              </div>
            </div>
            <div class="p-2 rounded-lg bg-surface-container-low flex items-start gap-2">
              <span class="material-symbols-outlined text-tertiary text-base">edit_note</span>
              <div>
                <p class="font-bold text-on-surface">3 Drafts Ready</p>
                <p class="text-on-surface-variant text-[11px]">AI Studio generated new variants.</p>
              </div>
            </div>
          </div>
        `;
        btn.appendChild(popover);
      }

      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        popover.classList.toggle('active');
      });
    });

    // Profile Dropdown Popover
    const profileAvatars = document.querySelectorAll('header img[alt*="Profile"], header img[alt*="avatar"], aside img[alt*="avatar"]');
    profileAvatars.forEach(avatar => {
      const parent = avatar.parentElement;
      if (parent) {
        parent.style.cursor = 'pointer';
        parent.title = 'Account Options';
        parent.addEventListener('click', (e) => {
          e.stopPropagation();
          openProfileModal();
        });
      }
    });

    // Global click listener to close popovers
    document.addEventListener('click', () => {
      document.querySelectorAll('.contently-popover.active').forEach(p => p.classList.remove('active'));
    });
  }

  function openQuickCreateModal() {
    let overlay = document.getElementById('quick-create-modal');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'quick-create-modal';
      overlay.className = 'contently-modal-overlay';
      overlay.innerHTML = `
        <div class="contently-modal-card p-6">
          <div class="flex items-center justify-between pb-4 border-b border-surface-container mb-4">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-primary text-2xl">add_circle</span>
              <h2 class="text-lg font-bold text-on-surface">Create Content</h2>
            </div>
            <button id="close-quick-create" class="text-outline hover:text-on-surface p-1 rounded-lg">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <p class="text-sm text-on-surface-variant mb-4">Choose an engine to start crafting your next content asset:</p>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
            <button class="quick-nav-opt p-4 rounded-xl border border-surface-container hover:border-primary bg-surface-container-lowest hover:bg-surface-container-low text-left transition-all" data-target="ai-studio">
              <span class="material-symbols-outlined text-primary text-xl mb-1 block">auto_awesome</span>
              <p class="font-bold text-sm text-on-surface">AI Studio Prompt</p>
              <p class="text-xs text-on-surface-variant">Synthesize multi-channel posts with brand voice.</p>
            </button>
            <button class="quick-nav-opt p-4 rounded-xl border border-surface-container hover:border-primary bg-surface-container-lowest hover:bg-surface-container-low text-left transition-all" data-target="content-editor">
              <span class="material-symbols-outlined text-secondary text-xl mb-1 block">edit_note</span>
              <p class="font-bold text-sm text-on-surface">Rich Content Editor</p>
              <p class="text-xs text-on-surface-variant">Long-form writing canvas with real-time stats.</p>
            </button>
            <button class="quick-nav-opt p-4 rounded-xl border border-surface-container hover:border-primary bg-surface-container-lowest hover:bg-surface-container-low text-left transition-all" data-target="templates">
              <span class="material-symbols-outlined text-tertiary text-xl mb-1 block">dashboard_customize</span>
              <p class="font-bold text-sm text-on-surface">Template Catalog</p>
              <p class="text-xs text-on-surface-variant">Start from 28 high-conversion proven frameworks.</p>
            </button>
            <button class="quick-nav-opt p-4 rounded-xl border border-surface-container hover:border-primary bg-surface-container-lowest hover:bg-surface-container-low text-left transition-all" data-target="content-repurposing">
              <span class="material-symbols-outlined text-primary-container text-xl mb-1 block">transform</span>
              <p class="font-bold text-sm text-on-surface">Content Repurposing</p>
              <p class="text-xs text-on-surface-variant">Transform one blog post into 5 platform formats.</p>
            </button>
          </div>
          <div class="flex justify-end">
            <button id="cancel-quick-create" class="px-4 py-2 rounded-xl text-sm font-semibold text-on-surface-variant hover:bg-surface-container">Cancel</button>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);

      overlay.querySelector('#close-quick-create').addEventListener('click', () => overlay.classList.remove('active'));
      overlay.querySelector('#cancel-quick-create').addEventListener('click', () => overlay.classList.remove('active'));
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('active');
      });

      overlay.querySelectorAll('.quick-nav-opt').forEach(btn => {
        btn.addEventListener('click', () => {
          overlay.classList.remove('active');
          const target = btn.getAttribute('data-target');
          navigateTo(target);
        });
      });
    }
    overlay.classList.add('active');
  }

  function openProfileModal() {
    const user = ContentlyAuth.getStoredUser() || DEFAULT_DEMO_USER;
    let overlay = document.getElementById('profile-modal');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'profile-modal';
      overlay.className = 'contently-modal-overlay';
      overlay.innerHTML = `
        <div class="contently-modal-card p-6">
          <div class="flex items-center justify-between pb-4 border-b border-surface-container mb-4">
            <div class="flex items-center gap-3">
              <img src="${user.avatar}" class="w-10 h-10 rounded-full object-cover ring-2 ring-primary/20" alt="Avatar"/>
              <div>
                <h2 class="text-base font-bold text-on-surface">${user.name}</h2>
                <p class="text-xs text-primary font-semibold">${user.role} · ${user.email}</p>
              </div>
            </div>
            <button id="close-profile-modal" class="text-outline hover:text-on-surface p-1 rounded-lg">
              <span class="material-symbols-outlined">close</span>
            </button>
          </div>
          <div class="space-y-2 mb-6 text-sm">
            <a href="${resolveUrl('profile-settings')}" class="flex items-center gap-2.5 p-3 rounded-xl hover:bg-surface-container-low text-on-surface transition-colors">
              <span class="material-symbols-outlined text-outline">manage_accounts</span>
              <span class="font-semibold flex-1">Account & Preferences</span>
              <span class="material-symbols-outlined text-outline text-sm">chevron_right</span>
            </a>
            <a href="${resolveUrl('brand-kit')}" class="flex items-center gap-2.5 p-3 rounded-xl hover:bg-surface-container-low text-on-surface transition-colors">
              <span class="material-symbols-outlined text-outline">palette</span>
              <span class="font-semibold flex-1">Brand Voice Settings</span>
              <span class="material-symbols-outlined text-outline text-sm">chevron_right</span>
            </a>
            <a href="${resolveUrl('landing')}" class="flex items-center gap-2.5 p-3 rounded-xl hover:bg-surface-container-low text-on-surface transition-colors">
              <span class="material-symbols-outlined text-outline">home</span>
              <span class="font-semibold flex-1">Return to Landing Page</span>
              <span class="material-symbols-outlined text-outline text-sm">chevron_right</span>
            </a>
          </div>
          <div class="pt-3 border-t border-surface-container flex items-center justify-between">
            <span class="text-xs text-outline">Demo Prototype Session</span>
            <button id="profile-modal-logout" class="px-4 py-2 rounded-xl text-sm font-bold text-error hover:bg-error-container/20 transition-colors flex items-center gap-1.5">
              <span class="material-symbols-outlined text-base">logout</span>
              <span>Log Out</span>
            </button>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);

      overlay.querySelector('#close-profile-modal').addEventListener('click', () => overlay.classList.remove('active'));
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('active');
      });

      overlay.querySelector('#profile-modal-logout').addEventListener('click', () => {
        overlay.classList.remove('active');
        ContentlyAuth.logout();
      });
    }
    overlay.classList.add('active');
  }

  // -------------------------------------------------------------------------
  // 7. PAGE-SPECIFIC INTERACTIVE ENHANCEMENTS
  // -------------------------------------------------------------------------
  function setupPageSpecificFeatures() {
    const currentKey = getCurrentRouteKey();

    // A. LOGIN PAGE
    if (currentKey === 'login') {
      const form = document.getElementById('loginForm');
      const emailInput = document.getElementById('email');
      const passwordInput = document.getElementById('password');
      const submitBtn = document.getElementById('submitButton');
      const btnText = document.getElementById('btnText');
      const btnIcon = document.getElementById('btnIcon');

      // Wire Google & GitHub OAuth buttons
      const googleBtn = document.getElementById('google-login-btn');
      if (googleBtn) {
        googleBtn.addEventListener('click', async (e) => {
          e.preventDefault();
          const provs = await ContentlyAuth.getProviders();
          if (provs?.google?.enabled) {
            window.location.href = '/api/auth/google/authorize';
          } else {
            ContentlyAuth.openOAuthModal('google', false);
          }
        });
      }
      const githubBtn = document.getElementById('github-login-btn');
      if (githubBtn) {
        githubBtn.addEventListener('click', async (e) => {
          e.preventDefault();
          const provs = await ContentlyAuth.getProviders();
          if (provs?.github?.enabled) {
            window.location.href = '/api/auth/github/authorize';
          } else {
            ContentlyAuth.openOAuthModal('github', false);
          }
        });
      }

      // Insert Demo Credentials Helper Card
      if (form && !document.getElementById('demo-credentials-helper')) {
        const helper = document.createElement('div');
        helper.id = 'demo-credentials-helper';
        helper.className = 'demo-credentials-card';
        helper.innerHTML = `
          <div>
            <p class="text-xs font-bold text-primary">Demo Prototype Access</p>
            <p class="text-[11px] text-on-surface-variant">demo@contently.local / ContentlyDemo123!</p>
          </div>
          <button type="button" id="autofill-demo-btn" class="px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold shadow-sm hover:bg-primary-container transition-all">
            Fill Demo
          </button>
        `;
        form.parentNode.insertBefore(helper, form);

        document.getElementById('autofill-demo-btn').addEventListener('click', () => {
          if (emailInput) emailInput.value = DEFAULT_DEMO_USER.email;
          if (passwordInput) passwordInput.value = DEFAULT_DEMO_USER.password;
          showToast('Demo credentials filled in!', 'success');
        });
      }

      // Wire login form submit
      if (form) {
        form.onsubmit = async function (e) {
          e.preventDefault();
          const email = emailInput ? emailInput.value.trim() : '';
          const password = passwordInput ? passwordInput.value : '';

          if (btnText) btnText.textContent = 'Authenticating Workspace...';
          if (btnIcon) {
            btnIcon.textContent = 'sync';
            btnIcon.classList.add('animate-spin');
          }
          if (submitBtn) submitBtn.classList.add('opacity-90', 'cursor-not-allowed');

          const result = await ContentlyAuth.login(email, password);
          if (result.success) {
            if (btnIcon) {
              btnIcon.classList.remove('animate-spin');
              btnIcon.textContent = 'check_circle';
            }
            if (btnText) btnText.textContent = 'Redirecting to Dashboard';
            showToast('Authenticated! Welcome to Contently Workspace.', 'success');
            setTimeout(() => {
              navigateTo('dashboard');
            }, 600);
          } else {
            if (btnIcon) {
              btnIcon.classList.remove('animate-spin');
              btnIcon.textContent = 'arrow_forward';
            }
            if (btnText) btnText.textContent = 'Log In to Contently';
            if (submitBtn) submitBtn.classList.remove('opacity-90', 'cursor-not-allowed');
            showToast(result.message, 'error');
          }
        };
      }

      // Wire "Sign up" switch link
      const signupLinks = findElementsByText('a', 'Sign up');
      signupLinks.forEach(link => {
        link.href = resolveUrl('signup');
        link.addEventListener('click', (e) => {
          e.preventDefault();
          navigateTo('signup');
        });
      });
    }

    // B. SIGNUP PAGE
    if (currentKey === 'signup') {
      const form = document.getElementById('signup-form') || document.querySelector('form');
      const nameInput = document.getElementById('fullName');
      const emailInput = document.getElementById('workEmail');
      const passwordInput = document.getElementById('password');
      const confirmPasswordInput = document.getElementById('confirmPassword');
      const submitBtn = form?.querySelector('button[type="submit"]');

      // Wire Google & GitHub OAuth buttons
      const googleBtn = document.getElementById('google-signup-btn');
      if (googleBtn) {
        googleBtn.addEventListener('click', async (e) => {
          e.preventDefault();
          const provs = await ContentlyAuth.getProviders();
          if (provs?.google?.enabled) {
            window.location.href = '/api/auth/google/authorize';
          } else {
            ContentlyAuth.openOAuthModal('google', true);
          }
        });
      }
      const githubBtn = document.getElementById('github-signup-btn');
      if (githubBtn) {
        githubBtn.addEventListener('click', async (e) => {
          e.preventDefault();
          const provs = await ContentlyAuth.getProviders();
          if (provs?.github?.enabled) {
            window.location.href = '/api/auth/github/authorize';
          } else {
            ContentlyAuth.openOAuthModal('github', true);
          }
        });
      }

      if (form) {
        form.onsubmit = async function (e) {
          e.preventDefault();
          const name = nameInput ? nameInput.value.trim() : 'Creator';
          const email = emailInput ? emailInput.value.trim() : '';
          const password = passwordInput ? passwordInput.value : '';
          const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';

          if (confirmPassword && password !== confirmPassword) {
            showToast('Passwords do not match. Please re-enter.', 'error');
            return;
          }

          if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add('opacity-90', 'cursor-not-allowed');
            const span = submitBtn.querySelector('span');
            if (span) span.textContent = 'Creating Account...';
          }

          const result = await ContentlyAuth.signup(name, email, password);
          if (result.success) {
            showToast(`Account created for ${name}! Opening workspace...`, 'success');
            setTimeout(() => {
              navigateTo('dashboard');
            }, 700);
          } else {
            if (submitBtn) {
              submitBtn.disabled = false;
              submitBtn.classList.remove('opacity-90', 'cursor-not-allowed');
              const span = submitBtn.querySelector('span');
              if (span) span.textContent = 'Create Account';
            }
            showToast(result.message, 'error');
          }
        };
      }

      // Wire "Log in" switch link
      const loginLinks = findElementsByText('a', 'Log in');
      loginLinks.forEach(link => {
        link.href = resolveUrl('login');
        link.addEventListener('click', (e) => {
          e.preventDefault();
          navigateTo('login');
        });
      });
    }

    // C. TEMPLATES PAGE
    if (currentKey === 'templates') {
      // Wire "Use Template" buttons
      const useTemplateBtns = document.querySelectorAll('.use-template-btn');
      const additionalTemplateBtns = findElementsByText('button', 'Use Template');
      const allUseBtns = new Set([...useTemplateBtns, ...additionalTemplateBtns]);

      allUseBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const card = btn.closest('.template-card') || btn.closest('article');
          const titleEl = card ? card.querySelector('h2') : null;
          const title = titleEl ? titleEl.textContent.trim() : 'Contrarian Thought Leader Framework';

          const sampleDraft = {
            title: title,
            format: 'LinkedIn Post',
            body: `Most industry leaders believe volume is king. Here is why the fastest 1% abandoned that playbook in 2025:

1. High-frequency noise degrades audience trust.
2. Calibrated resonance generates 3.4x higher organic conversion.
3. Autonomous AI guardrails maintain 100% brand tone fidelity.

What is your team's strategy for organic resonance this quarter?`
          };

          localStorage.setItem('contently_editor_draft', JSON.stringify(sampleDraft));
          showToast(`Selected "${title}". Opening in Content Editor...`, 'success');
          setTimeout(() => {
            navigateTo('content-editor');
          }, 600);
        });
      });

      // Filter tabs in template catalog
      const filterPills = document.querySelectorAll('#category-pills button');
      const cards = document.querySelectorAll('.template-card');
      filterPills.forEach(pill => {
        pill.addEventListener('click', () => {
          filterPills.forEach(p => {
            p.className = 'tab-btn px-space-md py-2 rounded-full font-label-md text-label-md bg-surface-container-lowest text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-all flex items-center gap-1.5 shadow-sm';
          });
          pill.className = 'tab-btn px-space-md py-2 rounded-full font-label-md text-label-md bg-primary text-on-primary shadow-sm hover:opacity-95 transition-all flex items-center gap-1.5';

          const category = pill.getAttribute('data-filter') || 'all';
          cards.forEach(card => {
            const cardCat = card.getAttribute('data-category') || '';
            if (category === 'all' || cardCat === category || category.includes(cardCat)) {
              card.style.display = 'flex';
            } else {
              card.style.display = 'none';
            }
          });
        });
      });

      // Live search input
      const searchInput = document.getElementById('template-search');
      if (searchInput) {
        searchInput.addEventListener('input', (e) => {
          const q = e.target.value.toLowerCase().trim();
          cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            card.style.display = text.includes(q) ? 'flex' : 'none';
          });
        });
      }
    }

    // D. CONTENT EDITOR PAGE
    if (currentKey === 'content-editor') {
      const titleInput = document.getElementById('editor-title');
      const editorArea = document.querySelector('[contenteditable="true"], textarea, #editorCanvas, main .prose');

      // Load draft from localStorage if present
      try {
        const savedDraft = localStorage.getItem('contently_editor_draft');
        if (savedDraft) {
          const draft = JSON.parse(savedDraft);
          if (titleInput && draft.title) titleInput.value = draft.title;
          if (editorArea && draft.body) {
            if (editorArea.tagName === 'TEXTAREA' || editorArea.tagName === 'INPUT') {
              editorArea.value = draft.body;
            } else {
              editorArea.innerText = draft.body;
            }
          }
          showToast(`Loaded draft: "${draft.title}"`, 'info');
        }
      } catch (err) {}

      // "Save Draft" button
      const saveButtons = findElementsByText('button', 'Save');
      saveButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          const title = titleInput ? titleInput.value : 'Untitled Content';
          showToast(`Draft "${title}" saved locally to Content Library.`, 'success');
        });
      });

      // "Publish Now" button
      const publishBtns = findElementsByText('button', 'Publish Now');
      publishBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          showToast('Simulated deployment complete: Content queued for distribution!', 'success');
        });
      });

      // "Copy Text" button
      const copyBtn = document.getElementById('copy-text-btn');
      if (copyBtn) {
        copyBtn.addEventListener('click', () => {
          const content = editorArea ? (editorArea.innerText || editorArea.value) : (titleInput ? titleInput.value : '');
          navigator.clipboard?.writeText(content).then(() => {
            showToast('Content copied to clipboard!', 'success');
          });
        });
      }
    }

    // E. CONTENT LIBRARY PAGE
    if (currentKey === 'content-library') {
      const searchInput = document.getElementById('librarySearchInput');
      const cards = document.querySelectorAll('.grid > div.rounded-xl, .grid > div.rounded-2xl');

      if (searchInput) {
        searchInput.addEventListener('input', (e) => {
          const q = e.target.value.toLowerCase().trim();
          cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            card.style.display = text.includes(q) ? '' : 'none';
          });
        });
      }

      // "New Draft" button navigates to Editor
      const newDraftBtns = findElementsByText('button', 'New Draft');
      newDraftBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          navigateTo('content-editor');
        });
      });
    }

    // F. AI STUDIO PAGE
    if (currentKey === 'ai-studio') {
      const outputCanvas = document.getElementById('outputCanvas');

      // Add "Open in Editor" button next to copy button
      if (outputCanvas && !document.getElementById('open-in-editor-btn')) {
        const actionsBar = outputCanvas.closest('.rounded-2xl')?.querySelector('.flex.items-center.gap-space-xs');
        if (actionsBar) {
          const openBtn = document.createElement('button');
          openBtn.id = 'open-in-editor-btn';
          openBtn.className = 'px-3 py-1.5 rounded-lg bg-primary-container text-white text-xs font-bold shadow-sm hover:opacity-90 flex items-center gap-1 transition-all';
          openBtn.innerHTML = `
            <span class="material-symbols-outlined text-sm">edit_note</span>
            <span>Open in Editor</span>
          `;
          openBtn.addEventListener('click', () => {
            const text = outputCanvas.innerText.trim();
            localStorage.setItem('contently_editor_draft', JSON.stringify({
              title: 'AI Studio Synthesized Post',
              format: 'LinkedIn Post',
              body: text
            }));
            showToast('Transferring to Content Editor...', 'success');
            setTimeout(() => navigateTo('content-editor'), 500);
          });
          actionsBar.appendChild(openBtn);
        }
      }
    }

    // G. BRAND KIT PAGE
    if (currentKey === 'brand-kit') {
      const saveBrandBtns = findElementsByText('button', 'Save');
      saveBrandBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          showToast('Brand Voice calibration updated & saved to local profile.', 'success');
        });
      });
    }

    // H. PROFILE & SETTINGS
    if (currentKey === 'profile-settings') {
      const saveSettingsBtns = findElementsByText('button', 'Save');
      saveSettingsBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          showToast('Preferences and account details updated successfully.', 'success');
        });
      });

      // Wire "Manage Subscription & Seats" button in Section 04
      const manageSubBtns = [
        document.getElementById('manage-subscription-btn'),
        ...findElementsByText('button', 'Manage Subscription')
      ].filter(Boolean);
      new Set(manageSubBtns).forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          ContentlyBilling.openSubscriptionPlansModal();
        });
      });

      // Synchronize live subscription details from backend
      ContentlyBilling.getSubscription().then(sub => {
        if (sub && sub.is_active) {
          const tierNameEl = document.getElementById('billing-tier-name');
          const tierPriceEl = document.getElementById('billing-plan-price');
          if (tierNameEl) tierNameEl.textContent = sub.tier_name || 'Pro Creator Tier';
          if (tierPriceEl) {
            if (sub.interval === 'yearly') {
              tierPriceEl.innerHTML = '₹38,390<span class="font-body-sm text-body-sm text-outline font-normal">/yr</span>';
            } else {
              tierPriceEl.innerHTML = '₹3,999<span class="font-body-sm text-body-sm text-outline font-normal">/mo</span>';
            }
          }
        }
      }).catch(() => {});
    }
  }

  // -------------------------------------------------------------------------
  // 8. ROUTE GUARDS & ACCESS CONTROL
  // -------------------------------------------------------------------------
  function enforceRouteGuard() {
    const currentKey = getCurrentRouteKey();
    const routeInfo = ROUTES[currentKey];

    // If route is protected and user is not logged in
    if (routeInfo && !routeInfo.public && !ContentlyAuth.isLoggedIn()) {
      showToast('Demo authentication required to access workspace. Redirecting...', 'warning', 2500);
      setTimeout(() => {
        navigateTo('login');
      }, 700);
      return false;
    }

    // If on login or signup and already logged in, redirect to dashboard
    if ((currentKey === 'login' || currentKey === 'signup') && ContentlyAuth.isLoggedIn()) {
      if (!window.location.search.includes('switch')) {
        showToast('Active demo session detected. Redirecting to Dashboard.', 'info', 2000);
        setTimeout(() => {
          navigateTo('dashboard');
        }, 600);
        return false;
      }
    }

    return true;
  }

  // -------------------------------------------------------------------------
  // 9. INITIALIZATION
  // -------------------------------------------------------------------------
  document.addEventListener('DOMContentLoaded', async () => {
    // 0. Handle OAuth redirect callback query params (?oauth_success=1&token=...)
    try {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.has('token')) {
        const token = urlParams.get('token');
        const provider = urlParams.get('provider') || 'OAuth';
        localStorage.setItem('contently_token', token);
        const meRes = await fetch('/api/auth/me', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (meRes.ok) {
          const userData = await meRes.json();
          localStorage.setItem('contently_demo_user', JSON.stringify(userData));
          window.history.replaceState({}, document.title, window.location.pathname);
          showToast(`Signed in with ${provider.charAt(0).toUpperCase() + provider.slice(1)}! Welcome, ${userData.name || userData.full_name}.`, 'success', 4000);
          if (window.location.pathname.includes('login') || window.location.pathname.includes('signup')) {
            navigateTo('dashboard');
            return;
          }
        }
      }
    } catch (e) {}

    // 1. Guard route
    const allowed = enforceRouteGuard();
    if (!allowed) return;

    // 2. Wire navigation links
    wireNavigation();

    // 3. Top Header interactions
    setupHeaderInteractions();

    // 4. Render demo indicator badge
    renderDemoIndicator();

    // 5. Setup page-specific features
    setupPageSpecificFeatures();
  });

  // Expose global demo APIs for console debugging
  window.Contently = {
    auth: ContentlyAuth,
    billing: ContentlyBilling,
    toast: showToast,
    navigate: navigateTo,
    resolveUrl: resolveUrl,
    currentRoute: getCurrentRouteKey
  };
})();
