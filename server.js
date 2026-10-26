const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const net = require('net');
const { spawn } = require('child_process');

const PORT = process.env.PORT || 3000;
const ROOT = __dirname;
const FRONTEND_ROOT = path.join(__dirname, 'frontend');
const BACKEND_HOST = process.env.BACKEND_HOST || '127.0.0.1';
const BACKEND_PORT = parseInt(process.env.BACKEND_PORT || '8000', 10);

// Clean route mappings to respective frontend code.html files
const ROUTE_MAP = {
  '/': 'landing/code.html',
  '/landing': 'landing/code.html',
  '/login': 'login/code.html',
  '/signup': 'signup/code.html',
  '/sign-up': 'signup/code.html',
  '/dashboard': 'dashboard/code.html',
  '/ai-studio': 'studio/code.html',
  '/studio': 'studio/code.html',
  '/templates': 'templates/code.html',
  '/content-library': 'library/code.html',
  '/library': 'library/code.html',
  '/content-editor': 'editor/code.html',
  '/editor': 'editor/code.html',
  '/content-planner': 'planner/code.html',
  '/planner': 'planner/code.html',
  '/content-repurposing': 'repurposing/code.html',
  '/repurposing': 'repurposing/code.html',
  '/seo-assistant': 'seo/code.html',
  '/seo': 'seo/code.html',
  '/brand-kit': 'brand-kit/code.html',
  '/profile-settings': 'settings/code.html',
  '/settings': 'settings/code.html',
  '/profile': 'settings/code.html',
  '/404': '404/code.html'
};

// Legacy folder name backward-compatibility rewrites
const LEGACY_FOLDER_MAP = {
  'landing_page_with_ambient_glow_celebration_contently': 'landing',
  'login_contently': 'login',
  'sign_up_contently': 'signup',
  'dashboard_with_ai_completion_celebrations_contently': 'dashboard',
  'ai_studio_contently': 'studio',
  'templates_contently': 'templates',
  'content_library_contently': 'library',
  'content_editor_contently': 'editor',
  'content_planner_contently': 'planner',
  'content_repurposing_contently': 'repurposing',
  'seo_assistant_contently': 'seo',
  'brand_kit_contently': 'brand-kit',
  'profile_and_settings_contently': 'settings',
  '404_contently': '404',
  'luminous_intelligence': 'design'
};

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.gif': 'image/gif',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.md': 'text/markdown; charset=utf-8'
};

// Forward requests starting with /api, /docs, /openapi.json to FastAPI
function proxyToBackend(req, res) {
  const options = {
    hostname: BACKEND_HOST,
    port: BACKEND_PORT,
    path: req.url,
    method: req.method,
    headers: {
      ...req.headers,
      host: `${BACKEND_HOST}:${BACKEND_PORT}`,
      'x-forwarded-host': req.headers.host || `localhost:${PORT}`,
      'x-forwarded-proto': 'http'
    }
  };

  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res, { end: true });
  });

  proxyReq.on('error', (err) => {
    res.writeHead(503, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({
      success: false,
      detail: 'Backend engine is starting up. Please try again in a moment.',
      error: err.message
    }));
  });

  req.pipe(proxyReq, { end: true });
}

const server = http.createServer((req, res) => {
  const parsedUrl = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  let pathname = decodeURIComponent(parsedUrl.pathname);

  // 0. API & Swagger docs proxying
  if (
    pathname.startsWith('/api/') ||
    pathname === '/api' ||
    pathname === '/docs' ||
    pathname.startsWith('/docs/') ||
    pathname === '/openapi.json' ||
    pathname === '/redoc' ||
    pathname.startsWith('/redoc/')
  ) {
    proxyToBackend(req, res);
    return;
  }

  // Normalize trailing slash if not root
  if (pathname.length > 1 && pathname.endsWith('/')) {
    pathname = pathname.slice(0, -1);
  }

  // 1. Check clean routes
  if (ROUTE_MAP[pathname]) {
    const targetFilePath = path.join(FRONTEND_ROOT, ROUTE_MAP[pathname]);
    serveFile(targetFilePath, res, 200);
    return;
  }

  // 1b. Check legacy folder paths (e.g. /login_contently/code.html -> frontend/login/code.html)
  for (const [legacy, clean] of Object.entries(LEGACY_FOLDER_MAP)) {
    if (pathname.includes(legacy)) {
      const rewritten = pathname.replace(legacy, clean);
      const targetFilePath = path.join(FRONTEND_ROOT, rewritten.replace(/^\//, ''));
      if (fs.existsSync(targetFilePath)) {
        serveFile(targetFilePath, res, 200);
        return;
      }
    }
  }

  // 2. Check static file paths in FRONTEND_ROOT first, then ROOT
  let filePath = path.join(FRONTEND_ROOT, pathname.replace(/^\//, ''));
  if (!fs.existsSync(filePath)) {
    filePath = path.join(ROOT, pathname.replace(/^\//, ''));
  }

  // Security check to prevent directory traversal
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403, { 'Content-Type': 'text/plain' });
    res.end('403 Forbidden');
    return;
  }

  fs.stat(filePath, (err, stats) => {
    if (!err && stats.isFile()) {
      serveFile(filePath, res, 200);
      return;
    }

    if (!err && stats.isDirectory()) {
      const codeHtml = path.join(filePath, 'code.html');
      const indexHtml = path.join(filePath, 'index.html');
      if (fs.existsSync(codeHtml)) {
        serveFile(codeHtml, res, 200);
        return;
      }
      if (fs.existsSync(indexHtml)) {
        serveFile(indexHtml, res, 200);
        return;
      }
    }

    // 3. Fallback to 404 page
    const notFoundPage = path.join(FRONTEND_ROOT, '404', 'code.html');
    if (fs.existsSync(notFoundPage)) {
      serveFile(notFoundPage, res, 404);
    } else {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('404 Not Found - Page does not exist');
    }
  });
});

function serveFile(filePath, res, statusCode) {
  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(500, { 'Content-Type': 'text/plain' });
      res.end('500 Internal Server Error');
      return;
    }
    res.writeHead(statusCode, {
      'Content-Type': contentType,
      'Cache-Control': 'no-cache'
    });
    res.end(data);
  });
}

// Function to check if a port is in use
function checkPortOpen(host, port) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    socket.setTimeout(800);
    socket.once('connect', () => {
      socket.destroy();
      resolve(true);
    });
    socket.once('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    socket.once('error', () => {
      resolve(false);
    });
    socket.connect(port, host);
  });
}

// Optional auto-start FastAPI backend if not already running
let backendProcess = null;

async function ensureBackendRunning() {
  const isRunning = await checkPortOpen(BACKEND_HOST, BACKEND_PORT);
  if (isRunning) {
    console.log(`📡 Backend API detected on http://${BACKEND_HOST}:${BACKEND_PORT}`);
    return;
  }

  console.log(`⚙️  Starting Contently Python FastAPI Backend on http://${BACKEND_HOST}:${BACKEND_PORT}...`);
  try {
    backendProcess = spawn(
      'python',
      ['-m', 'uvicorn', 'backend.app.main:app', '--host', BACKEND_HOST, '--port', String(BACKEND_PORT)],
      {
        cwd: ROOT,
        stdio: 'inherit',
        shell: true
      }
    );

    backendProcess.on('error', (err) => {
      console.warn('⚠️  Could not auto-start python backend:', err.message);
      console.warn('   You can start it manually: python -m uvicorn backend.app.main:app --port 8000');
    });
  } catch (err) {
    console.warn('⚠️  Failed to launch backend child process:', err.message);
  }
}

function cleanup() {
  if (backendProcess) {
    console.log('\n🛑 Shutting down backend process...');
    try {
      backendProcess.kill();
    } catch (e) {}
  }
  process.exit();
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
process.on('exit', cleanup);

server.listen(PORT, async () => {
  console.log(`\n======================================================`);
  console.log(`🚀 Contently AI Content Platform is running!`);
  console.log(`🌐 Frontend URL: http://localhost:${PORT}`);
  console.log(`📡 Backend API:   http://localhost:${PORT}/api/`);
  console.log(`📚 API Docs:     http://localhost:${PORT}/docs`);
  console.log(`🔑 Demo Account:`);
  console.log(`   Email: demo@contently.local`);
  console.log(`   Password: ContentlyDemo123!`);
  console.log(`======================================================\n`);

  await ensureBackendRunning();
});
