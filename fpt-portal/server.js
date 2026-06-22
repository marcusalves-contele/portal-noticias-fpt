// server.js — Express server do Portal FPT
require('dotenv').config({ path: '.env' });
const express = require('express');
const path = require('path');
const db = require('./db');

const app = express();
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.FPT_PORTAL_API_KEY || 'dev-key';

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// --- Middleware de autenticação ---
function requireApiKey(req, res, next) {
  const key = req.headers['x-api-key'];
  if (key !== API_KEY) return res.status(401).json({ error: 'Unauthorized' });
  next();
}

// --- Health check ---
app.get('/api/health', (req, res) => res.json({ ok: true }));

// --- API pública ---
app.get('/api/posts', async (req, res) => {
  const { category, limit = 20, offset = 0 } = req.query;
  const posts = await db.getPublished(Number(limit), Number(offset), category || null);
  res.json(posts);
});

app.get('/api/posts/:slug', async (req, res) => {
  const post = await db.getBySlug(req.params.slug);
  if (!post) return res.status(404).json({ error: 'Post não encontrado' });
  res.json(post);
});

// --- API PRISM OS (cria post pendente) ---
app.post('/api/posts', requireApiKey, async (req, res) => {
  const { title, slug, content_html, excerpt, image_url, video_id, category } = req.body;
  if (!title || !slug || !content_html) {
    return res.status(400).json({ error: 'title, slug e content_html são obrigatórios' });
  }
  try {
    const result = await db.createPost({ title, slug, content_html, excerpt, image_url, video_id, category });
    res.status(201).json({ id: result.lastID, slug, status: 'pending' });
  } catch (e) {
    if (e.message.includes('UNIQUE constraint')) return res.status(409).json({ error: 'Slug já existe' });
    res.status(500).json({ error: e.message });
  }
});

// --- API Admin ---
app.get('/api/admin/posts', requireApiKey, async (req, res) => {
  res.json(await db.getAll());
});

app.put('/api/admin/posts/:id/publish', requireApiKey, async (req, res) => {
  await db.publish(Number(req.params.id));
  res.json({ ok: true });
});

app.put('/api/admin/posts/:id/reject', requireApiKey, async (req, res) => {
  await db.reject(Number(req.params.id));
  res.json({ ok: true });
});

// --- Rotas HTML ---
app.get('/post/:slug', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'post.html'));
});

app.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'admin.html'));
});

app.listen(PORT, () => {
  console.log(`Portal FPT rodando em http://localhost:${PORT}`);
});
