const isAdmin = window.location.pathname.startsWith('/admin');

const defaultConfig = {
  name: 'Hade',
  description: 'Cinematic web creator building immersive interfaces and premium digital vibes.',
  place: 'Morocco',
  availability: 'AVAILABLE NOW',
  pfp: '/static/assets/pfp.svg',
  video: '',
  music: '',
  accentColor: '#8e77ff',
  links: [
    { label: 'Instagram', url: '#' },
    { label: 'GitHub', url: '#' }
  ],
  skills: ['UI/UX', 'Motion', 'Frontend', 'Branding', 'Creative Coding'],
  projects: [
    { title: 'Cinematic Identity Landing', description: 'Dark visual-first personal page with premium interactions.' }
  ]
};

async function api(path, options) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error || 'Request failed');
  }
  return data;
}

function setAccent(color) {
  if (!color) return;
  document.documentElement.style.setProperty('--accent', color);
}

function renderPortfolio(config) {
  const byId = (id) => document.getElementById(id);
  byId('name').textContent = config.name;
  byId('description').textContent = config.description;
  byId('place').textContent = `📍 ${config.place}`;
  byId('availability').textContent = config.availability;
  byId('pfp').src = config.pfp || defaultConfig.pfp;
  document.title = `${config.name} — Live Portfolio`;
  setAccent(config.accentColor);

  const skillsRoot = byId('skills');
  skillsRoot.innerHTML = (config.skills || []).map((item) => `<span>${item}</span>`).join('');

  const projectsRoot = byId('projects');
  projectsRoot.innerHTML = (config.projects || [])
    .map(
      (project) => `
      <article class="project">
        <h3>${project.title || ''}</h3>
        <p>${project.description || ''}</p>
      </article>
    `
    )
    .join('');

  const linksRoot = byId('links');
  linksRoot.innerHTML = (config.links || [])
    .map((link) => `<a href="${link.url || '#'}" target="_blank" rel="noreferrer">${link.label || 'Link'}</a>`)
    .join('');

  const music = byId('bg-music');
  const toggle = byId('music-toggle');
  music.src = config.music || '';
  let playing = false;

  toggle.addEventListener('click', async () => {
    if (!config.music) {
      toggle.textContent = 'No music URL';
      return;
    }

    if (playing) {
      music.pause();
      playing = false;
      toggle.textContent = '🔇 Music Off';
      return;
    }

    try {
      await music.play();
      playing = true;
      toggle.textContent = '🎵 Music On';
    } catch {
      toggle.textContent = 'Click again';
    }
  });
}

function setupContactForm() {
  const form = document.getElementById('contact-form');
  if (!form) return;

  const status = document.getElementById('contact-status');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
      name: document.getElementById('contact-name').value.trim(),
      email: document.getElementById('contact-email').value.trim(),
      message: document.getElementById('contact-message').value.trim()
    };

    try {
      await api('/api/contact', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      status.textContent = '✅ Message sent live to backend inbox.';
      form.reset();
    } catch (error) {
      status.textContent = `❌ ${error.message}`;
    }
  });
}

function fillAdmin(config) {
  const setValue = (id, value) => {
    const input = document.getElementById(id);
    if (input) input.value = value;
  };

  setValue('name', config.name || '');
  setValue('description', config.description || '');
  setValue('place', config.place || '');
  setValue('availability', config.availability || '');
  setValue('pfp', config.pfp || '');
  setValue('music', config.music || '');
  setValue('accentColor', config.accentColor || '');
  setValue('skills', (config.skills || []).join(', '));
  setValue('links', JSON.stringify(config.links || [], null, 2));
  setValue('projects', JSON.stringify(config.projects || [], null, 2));
}

function collectAdmin() {
  const read = (id) => document.getElementById(id).value;
  return {
    name: read('name').trim(),
    description: read('description').trim(),
    place: read('place').trim(),
    availability: read('availability').trim(),
    pfp: read('pfp').trim(),
    music: read('music').trim(),
    accentColor: read('accentColor').trim(),
    skills: read('skills').split(',').map((x) => x.trim()).filter(Boolean),
    links: JSON.parse(read('links')),
    projects: JSON.parse(read('projects'))
  };
}

function renderMessages(messages) {
  const root = document.getElementById('messages');
  root.innerHTML = messages
    .map(
      (item) => `
      <article class="message">
        <div class="top">
          <span><b>${item.name}</b> • ${item.email}</span>
          <span>${new Date(item.created_at).toLocaleString()}</span>
        </div>
        <p>${item.message}</p>
      </article>
    `
    )
    .join('');
}

async function setupAdmin() {
  const status = document.getElementById('admin-status');
  const form = document.getElementById('admin-form');
  const reload = document.getElementById('reload-config');
  const refresh = document.getElementById('refresh-messages');

  async function loadAll() {
    const config = await api('/api/config');
    fillAdmin({ ...defaultConfig, ...config });
    const messages = await api('/api/messages');
    renderMessages(messages);
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      const payload = collectAdmin();
      await api('/api/config', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      status.textContent = '✅ Saved to Flask backend.';
    } catch (error) {
      status.textContent = `❌ ${error.message}`;
    }
  });

  reload.addEventListener('click', async () => {
    try {
      await loadAll();
      status.textContent = '✅ Reloaded config and inbox.';
    } catch (error) {
      status.textContent = `❌ ${error.message}`;
    }
  });

  refresh.addEventListener('click', async () => {
    try {
      const messages = await api('/api/messages');
      renderMessages(messages);
      status.textContent = '✅ Inbox refreshed.';
    } catch (error) {
      status.textContent = `❌ ${error.message}`;
    }
  });

  await loadAll();
}

async function setupPortfolio() {
  const config = await api('/api/config');
  renderPortfolio({ ...defaultConfig, ...config });
  setupContactForm();
}

(async function init() {
  try {
    if (isAdmin) {
      await setupAdmin();
      return;
    }
    await setupPortfolio();
  } catch (error) {
    console.error(error);
  }
})();
