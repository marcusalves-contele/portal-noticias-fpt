// server.js — Express server do Portal FPT
require('dotenv').config({ path: '.env' });
const express = require('express');
const path = require('path');
const https = require('https');
const nodemailer = require('nodemailer');
const cron = require('node-cron');
const db = require('./db');
const sponsors = require('./sponsors');

// Canal do Julio César — Frota Para Todos
const JULIO_CHANNEL_ID = process.env.JULIO_CHANNEL_ID || 'UCz31CtOANqSFuLEdFTi1iCQ';
const YOUTUBE_RSS = `https://www.youtube.com/feeds/videos.xml?channel_id=${JULIO_CHANNEL_ID}`;

const app = express();
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.FPT_PORTAL_API_KEY || 'dev-key';

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// --- Email transporter ---
const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST || 'smtp.gmail.com',
  port: Number(process.env.SMTP_PORT) || 587,
  secure: false,
  auth: {
    user: process.env.SMTP_USER || '',
    pass: process.env.SMTP_PASS || '',
  },
});

// --- Middleware de autenticação ---
function requireApiKey(req, res, next) {
  const key = req.headers['x-api-key'];
  if (key !== API_KEY) return res.status(401).json({ error: 'Unauthorized' });
  next();
}

// --- Health check ---
app.get('/api/health', (req, res) => res.json({ ok: true }));

// --- Patrocinadores ---
app.get('/api/sponsors', (req, res) => res.json(sponsors));

// --- API pública — Posts ---
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

// --- Busca ---
app.get('/api/search', async (req, res) => {
  const { q, limit = 10 } = req.query;
  if (!q || q.trim().length < 2) return res.json([]);
  try {
    const maxLimit = Math.min(Number(limit) || 10, 100);
    const results = await db.search(q.trim(), maxLimit);
    res.json(results);
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/posts/related/:slug', async (req, res) => {
  try {
    const post = await db.getBySlug(req.params.slug);
    if (!post) return res.json([]);
    const related = await db.getRelated(post.slug, post.category);
    res.json(related);
  } catch (e) {
    res.json([]);
  }
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

// --- API Admin — Posts ---
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

// --- Newsletter ---
app.post('/api/newsletter/subscribe', async (req, res) => {
  const { email } = req.body;
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: 'Email inválido' });
  }
  try {
    await db.subscribe(email.toLowerCase().trim());
    res.status(201).json({ ok: true, message: 'Inscrito com sucesso!' });
  } catch (e) {
    if (e.message.includes('UNIQUE constraint')) {
      return res.status(409).json({ error: 'Email já cadastrado' });
    }
    res.status(500).json({ error: e.message });
  }
});

app.post('/api/newsletter/unsubscribe', async (req, res) => {
  const { email } = req.body;
  await db.unsubscribe(email);
  res.json({ ok: true });
});

app.get('/api/admin/subscribers', requireApiKey, async (req, res) => {
  res.json(await db.getActiveSubscribers());
});

// Envio manual da newsletter (ou chamado pelo cron)
async function sendWeeklyNewsletter() {
  if (!process.env.SMTP_USER) {
    console.log('[Newsletter] SMTP não configurado — pulando envio');
    return { sent: 0, skipped: true };
  }

  const posts = await db.getRecentPublished(5);
  const subscribers = await db.getActiveSubscribers();

  if (!posts.length || !subscribers.length) {
    console.log('[Newsletter] Sem posts ou inscritos — pulando');
    return { sent: 0 };
  }

  const postsHtml = posts.map(p => `
    <tr>
      <td style="padding:16px 0;border-bottom:1px solid #1e1035;">
        <a href="${process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br'}/post/${p.slug}"
           style="font-size:16px;font-weight:700;color:#8B23E5;text-decoration:none;">${p.title}</a>
        <p style="margin:8px 0 0;font-size:14px;color:#94A3B8;">${p.excerpt || ''}</p>
      </td>
    </tr>`).join('');

  const html = `
    <!DOCTYPE html>
    <html>
    <body style="background:#080010;color:#F7F7F7;font-family:Arial,sans-serif;margin:0;padding:0;">
      <table width="600" align="center" style="padding:32px 24px;">
        <tr>
          <td style="padding-bottom:24px;border-bottom:2px solid #8B23E5;">
            <span style="font-size:22px;font-weight:800;color:#F7F7F7;">Frota Para <span style="color:#8B23E5;">Todos</span></span>
            <span style="font-size:14px;color:#94A3B8;margin-left:12px;">Curadoria semanal</span>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 0 8px;">
            <p style="font-size:15px;color:#94A3B8;">Os artigos mais relevantes desta semana para gestores de frota:</p>
          </td>
        </tr>
        ${postsHtml}
        <tr>
          <td style="padding:32px 0 16px;border-top:1px solid #1e1035;">
            <a href="${process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br'}"
               style="background:linear-gradient(135deg,#8B23E5,#b56fff);color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">
              Ver todos os artigos →
            </a>
          </td>
        </tr>
        <tr>
          <td style="padding-top:24px;">
            <p style="font-size:12px;color:#4a4a6a;">
              Patrocinado por <a href="https://contelerastreador.com.br" style="color:#8B23E5;">Contele Fleet</a> ·
              <a href="{{unsubscribe_url}}" style="color:#4a4a6a;">Cancelar inscrição</a>
            </p>
          </td>
        </tr>
      </table>
    </body>
    </html>`;

  let sent = 0;
  for (const sub of subscribers) {
    try {
      const personalizedHtml = html.replace('{{unsubscribe_url}}',
        `${process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br'}/unsubscribe?email=${encodeURIComponent(sub.email)}`);
      await transporter.sendMail({
        from: `"Frota Para Todos" <${process.env.SMTP_USER}>`,
        to: sub.email,
        subject: `📦 Curadoria FPT — ${new Date().toLocaleDateString('pt-BR', { day: '2-digit', month: 'long' })}`,
        html: personalizedHtml,
      });
      sent++;
    } catch (e) {
      console.error(`[Newsletter] Erro ao enviar para ${sub.email}:`, e.message);
    }
  }
  console.log(`[Newsletter] Enviado para ${sent}/${subscribers.length} inscritos`);
  return { sent, total: subscribers.length };
}

// Cron: toda segunda-feira às 8h
cron.schedule('0 8 * * 1', sendWeeklyNewsletter, { timezone: 'America/Sao_Paulo' });

// --- Sincronização YouTube RSS ---
function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

function parseYouTubeRSS(xml) {
  const entries = [];
  const entryRegex = /<entry>([\s\S]*?)<\/entry>/g;
  let match;
  while ((match = entryRegex.exec(xml)) !== null) {
    const entry = match[1];
    const videoId = (entry.match(/<yt:videoId>(.*?)<\/yt:videoId>/) || [])[1];
    const title = (entry.match(/<title>(.*?)<\/title>/) || [])[1];
    const published = (entry.match(/<published>(.*?)<\/published>/) || [])[1];
    const description = (entry.match(/<media:description>([\s\S]*?)<\/media:description>/) || [])[1] || '';
    if (videoId && title) {
      entries.push({
        video_id: videoId,
        title: title.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&#39;/g, "'").replace(/&quot;/g, '"'),
        published_at: published,
        excerpt: description.replace(/<[^>]+>/g, '').substring(0, 300).trim(),
        image_url: `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`,
      });
    }
  }
  return entries;
}

function toSlug(title) {
  return title
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .substring(0, 80);
}

async function syncYouTubeVideos() {
  console.log('[YouTube Sync] Verificando novos vídeos...');
  try {
    const xml = await fetchUrl(YOUTUBE_RSS);
    const videos = parseYouTubeRSS(xml);
    console.log(`[YouTube Sync] ${videos.length} vídeos encontrados no canal`);

    let criados = 0;
    for (const video of videos) {
      const slug = toSlug(video.title);
      // Verifica se já existe pelo video_id ou slug
      const existing = await db.getByVideoId(video.video_id);
      if (existing) continue;

      await db.createPost({
        title: video.title,
        slug,
        content_html: `<p>${video.excerpt || 'Assista ao vídeo completo acima.'}</p>`,
        excerpt: video.excerpt ? video.excerpt.substring(0, 200) : '',
        image_url: video.image_url,
        video_id: video.video_id,
        category: 'videos',
      });
      criados++;
      console.log(`[YouTube Sync] Novo post criado: "${video.title}" (${video.video_id})`);
    }

    if (criados > 0) {
      console.log(`[YouTube Sync] ${criados} novo(s) post(s) pendente(s) de aprovação no admin`);
    } else {
      console.log('[YouTube Sync] Nenhum vídeo novo encontrado');
    }
    return { criados, total: videos.length };
  } catch (e) {
    console.error('[YouTube Sync] Erro:', e.message);
    return { erro: e.message };
  }
}

// Cron: todo dia às 7h verifica novos vídeos no YouTube
cron.schedule('0 7 * * *', syncYouTubeVideos, { timezone: 'America/Sao_Paulo' });

// Endpoint manual para forçar sync
app.post('/api/admin/sync-youtube', requireApiKey, async (req, res) => {
  const result = await syncYouTubeVideos();
  res.json(result);
});

app.post('/api/admin/newsletter/send', requireApiKey, async (req, res) => {
  const result = await sendWeeklyNewsletter();
  res.json(result);
});

// --- Comentários ---
app.get('/api/comments/:slug', async (req, res) => {
  const comments = await db.getApprovedComments(req.params.slug);
  res.json(comments);
});

app.post('/api/comments', async (req, res) => {
  const { post_id, post_slug, author, content } = req.body;
  if (!post_slug || !author || !content) {
    return res.status(400).json({ error: 'post_slug, author e content são obrigatórios' });
  }
  if (content.length > 2000) {
    return res.status(400).json({ error: 'Comentário muito longo (máx 2000 chars)' });
  }
  const result = await db.createComment({ post_id: post_id || 0, post_slug, author: author.trim(), content: content.trim() });
  res.status(201).json({ id: result.lastID, status: 'pending', message: 'Comentário enviado para moderação' });
});

app.get('/api/admin/comments', requireApiKey, async (req, res) => {
  res.json(await db.getAllComments());
});

app.put('/api/admin/comments/:id/approve', requireApiKey, async (req, res) => {
  await db.approveComment(Number(req.params.id));
  res.json({ ok: true });
});

app.put('/api/admin/comments/:id/reject', requireApiKey, async (req, res) => {
  await db.rejectComment(Number(req.params.id));
  res.json({ ok: true });
});

// --- Rotas HTML ---
app.get('/post/:slug', (req, res) => res.sendFile(path.join(__dirname, 'public', 'post.html')));
app.get('/admin', (req, res) => res.sendFile(path.join(__dirname, 'public', 'admin.html')));
app.get('/unsubscribe', (req, res) => res.sendFile(path.join(__dirname, 'public', 'unsubscribe.html')));
app.get('/about', (req, res) => res.sendFile(path.join(__dirname, 'public', 'about.html')));

app.get('/sitemap.xml', async (req, res) => {
  const base = process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br';
  try {
    const posts = await db.getPublished(1000, 0, null);
    const staticUrls = [
      `<url><loc>${base}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>`,
      `<url><loc>${base}/about</loc><changefreq>monthly</changefreq><priority>0.6</priority></url>`,
    ];
    const postUrls = posts.map(p => {
      const lastmod = p.published_at ? p.published_at.substring(0, 10) : '';
      return `<url><loc>${base}/post/${p.slug}</loc>${lastmod ? `<lastmod>${lastmod}</lastmod>` : ''}<changefreq>monthly</changefreq><priority>0.8</priority></url>`;
    });
    res.setHeader('Content-Type', 'application/xml; charset=utf-8');
    res.send(`<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${[...staticUrls, ...postUrls].join('\n  ')}
</urlset>`);
  } catch (e) {
    res.status(500).send('Erro ao gerar sitemap');
  }
});

app.listen(PORT, () => {
  console.log(`Portal FPT rodando em http://localhost:${PORT}`);
});
