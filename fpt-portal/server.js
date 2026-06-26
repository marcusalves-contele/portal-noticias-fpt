// server.js — Express server do Portal FPT
require('dotenv').config({ path: '.env' });
const express = require('express');
const compression = require('compression');
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
app.set('trust proxy', 1);
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.FPT_PORTAL_API_KEY || 'dev-key';
const HMAC_SECRET = process.env.HMAC_SECRET || 'fpt-portal-hmac-secret-dev';
const crypto = require('crypto');
function unsubscribeToken(email) {
  return crypto.createHmac('sha256', HMAC_SECRET).update(email.toLowerCase()).digest('hex');
}

app.use(compression({ threshold: 1024 }));
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

app.get('/api/posts/popular', async (req, res) => {
  const { limit = 5 } = req.query;
  const posts = await db.getPopular(Math.min(Number(limit) || 5, 20));
  res.json(posts);
});

app.get('/api/posts/featured', async (req, res) => {
  const post = await db.getFeatured();
  res.json(post || null);
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

// --- Tracking de views ---
app.post('/api/posts/:slug/view', async (req, res) => {
  try {
    await db.incrementView(req.params.slug);
    res.json({ ok: true });
  } catch (e) {
    res.json({ ok: false });
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

app.delete('/api/admin/posts/:id', requireApiKey, async (req, res) => {
  try {
    const result = await db.deletePost(Number(req.params.id));
    if (result.changes === 0) return res.status(404).json({ error: 'Post não encontrado' });
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.put('/api/admin/posts/:id', requireApiKey, async (req, res) => {
  const { title, excerpt, content_html, category, featured, difficulty, summary_points, image_url } = req.body;
  if (!title || !content_html) {
    return res.status(400).json({ error: 'title e content_html são obrigatórios' });
  }
  try {
    const result = await db.updatePost(Number(req.params.id), { title, excerpt, content_html, category, featured, difficulty, summary_points, image_url });
    if (result.changes === 0) return res.status(404).json({ error: 'Post não encontrado' });
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// Notificar inscritos sobre um post específico
app.post('/api/admin/posts/:id/notify', requireApiKey, async (req, res) => {
  if (!process.env.SMTP_USER) return res.json({ sent: 0, skipped: true, reason: 'SMTP não configurado' });
  try {
    const post = await db.getBySlug(
      await (async () => {
        const rows = await db.getAll();
        const found = rows.find(p => p.id === Number(req.params.id));
        return found ? found.slug : null;
      })()
    );
    if (!post) return res.status(404).json({ error: 'Post não encontrado ou não publicado' });
    const subscribers = await db.getConfirmedSubscribers();
    if (!subscribers.length) return res.json({ sent: 0, reason: 'Sem inscritos confirmados' });
    const base = process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br';
    const img = post.image_url || (post.video_id ? `https://img.youtube.com/vi/${post.video_id}/hqdefault.jpg` : '');
    let sent = 0;
    for (const sub of subscribers) {
      try {
        const token = unsubscribeToken(sub.email);
        await transporter.sendMail({
          from: `"Frota Para Todos" <${process.env.SMTP_USER}>`,
          to: sub.email,
          subject: `📰 ${post.title} — Frota Para Todos`,
          html: `<!DOCTYPE html><html><body style="background:#080010;color:#F7F7F7;font-family:Arial,sans-serif;margin:0;padding:0;">
            <table width="600" align="center" style="padding:32px 24px;">
              <tr><td style="padding-bottom:24px;border-bottom:2px solid #8B23E5;">
                <span style="font-size:22px;font-weight:800;color:#F7F7F7;">Frota Para <span style="color:#8B23E5;">Todos</span></span>
              </td></tr>
              <tr><td style="padding:24px 0;">
                ${img ? `<img src="${img}" style="width:100%;border-radius:8px;margin-bottom:16px;" alt="${post.title}">` : ''}
                <p style="font-size:13px;color:#8B23E5;text-transform:uppercase;letter-spacing:1px;margin:0 0 8px;">Novo artigo</p>
                <h2 style="font-size:22px;font-weight:800;margin:0 0 12px;color:#F7F7F7;">${post.title}</h2>
                ${post.excerpt ? `<p style="font-size:14px;color:#94A3B8;margin:0 0 20px;">${post.excerpt}</p>` : ''}
                <a href="${base}/post/${post.slug}" style="background:linear-gradient(135deg,#8B23E5,#b56fff);color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">Ler artigo completo →</a>
              </td></tr>
              <tr><td style="padding-top:24px;"><p style="font-size:12px;color:#4a4a6a;">
                Patrocinado por <a href="https://contelerastreador.com.br" style="color:#8B23E5;">Contele Fleet</a> ·
                <a href="${base}/unsubscribe?email=${encodeURIComponent(sub.email)}&token=${token}" style="color:#4a4a6a;">Cancelar inscrição</a>
              </p></td></tr>
            </table></body></html>`,
        });
        sent++;
      } catch (e) {
        console.error(`[Notify] Erro ao enviar para ${sub.email}:`, e.message);
      }
    }
    console.log(`[Notify] Post "${post.title}" notificado para ${sent}/${subscribers.length} inscritos`);
    res.json({ sent, total: subscribers.length });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

app.put('/api/admin/posts/:id/schedule', requireApiKey, async (req, res) => {
  const { scheduled_at } = req.body;
  if (!scheduled_at) return res.status(400).json({ error: 'scheduled_at obrigatório' });
  try {
    await db.setScheduled(Number(req.params.id), scheduled_at);
    res.json({ ok: true });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});

// --- Newsletter ---
async function sendConfirmationEmail(email, token) {
  if (!process.env.SMTP_USER) return;
  const portalUrl = process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br';
  const confirmUrl = `${portalUrl}/api/newsletter/confirm?token=${token}`;
  await transporter.sendMail({
    from: `"Frota Para Todos" <${process.env.SMTP_USER}>`,
    to: email,
    subject: 'Confirme sua inscrição na newsletter — Frota Para Todos',
    html: `
      <!DOCTYPE html>
      <html>
      <body style="background:#080010;color:#F7F7F7;font-family:Arial,sans-serif;margin:0;padding:0;">
        <table width="600" align="center" style="padding:32px 24px;">
          <tr>
            <td style="padding-bottom:24px;border-bottom:2px solid #8B23E5;">
              <span style="font-size:22px;font-weight:800;color:#F7F7F7;">Frota Para <span style="color:#8B23E5;">Todos</span></span>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 0;">
              <p style="font-size:16px;color:#F7F7F7;margin:0 0 16px;">Obrigado por se inscrever!</p>
              <p style="font-size:14px;color:#94A3B8;margin:0 0 24px;">Clique no botão abaixo para confirmar sua inscrição e começar a receber a curadoria semanal para gestores de frota.</p>
              <a href="${confirmUrl}"
                 style="background:linear-gradient(135deg,#8B23E5,#b56fff);color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px;">
                Confirmar inscrição →
              </a>
              <p style="font-size:12px;color:#4a4a6a;margin-top:24px;">Se você não solicitou essa inscrição, ignore este email.</p>
            </td>
          </tr>
        </table>
      </body>
      </html>`,
  });
}

app.post('/api/newsletter/subscribe', async (req, res) => {
  const { email } = req.body;
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return res.status(400).json({ error: 'Email inválido' });
  }
  const normalizedEmail = email.toLowerCase().trim();
  try {
    const existing = await db.getSubscriberByEmail(normalizedEmail);
    if (existing) {
      if (existing.active === 1) {
        return res.status(409).json({ error: 'Email já cadastrado' });
      }
      await db.reactivateSubscriber(normalizedEmail);
    } else {
      await db.subscribe(normalizedEmail);
    }
    const token = crypto.randomBytes(32).toString('hex');
    await db.setConfirmToken(normalizedEmail, token);
    sendConfirmationEmail(normalizedEmail, token).catch(e =>
      console.error('[Newsletter] Erro ao enviar email de confirmação:', e.message)
    );
    res.status(201).json({ ok: true, message: 'Quase lá! Verifique seu email para confirmar a inscrição.' });
  } catch (e) {
    if (e.message.includes('UNIQUE constraint')) {
      return res.status(409).json({ error: 'Email já cadastrado' });
    }
    res.status(500).json({ error: e.message });
  }
});

app.get('/api/newsletter/confirm', async (req, res) => {
  const { token } = req.query;
  if (!token) return res.status(400).send('Token inválido.');
  try {
    const result = await db.confirmSubscriber(token);
    if (result.changes === 0) {
      return res.status(400).send('Link expirado ou já utilizado.');
    }
    const portalUrl = process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br';
    res.redirect(`${portalUrl}/?confirmed=1`);
  } catch (e) {
    res.status(500).send('Erro ao confirmar inscrição.');
  }
});

app.post('/api/newsletter/unsubscribe', async (req, res) => {
  const { email, token } = req.body;
  if (!email || !token) return res.status(400).json({ error: 'email e token obrigatórios' });
  const expected = unsubscribeToken(email);
  if (token !== expected) return res.status(403).json({ error: 'Token inválido' });
  await db.unsubscribe(email.toLowerCase().trim());
  res.json({ ok: true });
});

app.get('/api/admin/subscribers', requireApiKey, async (req, res) => {
  const [all, confirmed] = await Promise.all([
    db.getActiveSubscribers(),
    db.getConfirmedSubscribers(),
  ]);
  res.json({ total: all.length, confirmed: confirmed.length, pending: all.length - confirmed.length, subscribers: all });
});

// Envio manual da newsletter (ou chamado pelo cron)
async function sendWeeklyNewsletter() {
  if (!process.env.SMTP_USER) {
    console.log('[Newsletter] SMTP não configurado — pulando envio');
    return { sent: 0, skipped: true };
  }

  const posts = await db.getRecentPublished(5);
  const subscribers = await db.getConfirmedSubscribers();

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
      const token = unsubscribeToken(sub.email);
      const personalizedHtml = html.replace('{{unsubscribe_url}}',
        `${process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br'}/unsubscribe?email=${encodeURIComponent(sub.email)}&token=${token}`);
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
        image_url: `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`,
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

      try {
        let finalSlug = slug || `video-${video.video_id}`;
        let attempt = 0;
        while (attempt < 5) {
          try {
            await db.createPost({
              title: video.title,
              slug: finalSlug,
              content_html: `<p>${video.excerpt || 'Assista ao vídeo completo acima.'}</p>`,
              excerpt: video.excerpt ? video.excerpt.substring(0, 200) : '',
              image_url: video.image_url,
              video_id: video.video_id,
              category: 'videos',
            });
            criados++;
            console.log(`[YouTube Sync] Novo post criado: "${video.title}" (${video.video_id})`);
            break;
          } catch (innerErr) {
            if (innerErr.message.includes('UNIQUE constraint') && attempt < 4) {
              attempt++;
              finalSlug = `${slug}-${attempt}`;
            } else {
              throw innerErr;
            }
          }
        }
      } catch (e) {
        console.error(`[YouTube Sync] Erro ao criar post "${video.title}":`, e.message);
      }
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

// Cron: a cada 5 minutos, publica posts agendados
cron.schedule('*/5 * * * *', async () => {
  try {
    const scheduled = await db.getScheduled();
    for (const post of scheduled) {
      await db.publish(post.id);
      console.log(`[Scheduler] Post publicado: "${post.title}" (id=${post.id})`);
    }
  } catch (e) {
    console.error('[Scheduler] Erro:', e.message);
  }
}, { timezone: 'America/Sao_Paulo' });

// Endpoint manual para forçar sync
app.post('/api/admin/sync-youtube', requireApiKey, async (req, res) => {
  const result = await syncYouTubeVideos();
  res.json(result);
});

app.get('/api/admin/analytics/views', requireApiKey, async (req, res) => {
  const stats = await db.getViewsStats();
  res.json(stats);
});

app.post('/api/admin/newsletter/send', requireApiKey, async (req, res) => {
  const result = await sendWeeklyNewsletter();
  res.json(result);
});

// --- Helpers de segurança ---
function stripHtml(str) {
  return String(str).replace(/<[^>]*>/g, '').trim();
}

// --- Rate limiting (in-memory) ---
const commentRateLimit = new Map(); // ip -> { count, resetAt }
function checkCommentRateLimit(ip) {
  const now = Date.now();
  const entry = commentRateLimit.get(ip);
  if (!entry || now > entry.resetAt) {
    commentRateLimit.set(ip, { count: 1, resetAt: now + 60 * 60 * 1000 });
    return true; // OK
  }
  if (entry.count >= 5) return false; // bloqueado
  entry.count++;
  return true; // OK
}

// Cleanup expired rate limit entries every 2 hours
setInterval(() => {
  const now = Date.now();
  for (const [ip, entry] of commentRateLimit.entries()) {
    if (now > entry.resetAt) commentRateLimit.delete(ip);
  }
}, 2 * 60 * 60 * 1000);

// --- Comentários ---
app.get('/api/comments/:slug', async (req, res) => {
  const comments = await db.getApprovedComments(req.params.slug);
  res.json(comments);
});

app.post('/api/comments', async (req, res) => {
  const ip = req.ip || req.connection.remoteAddress || 'unknown';
  if (!checkCommentRateLimit(ip)) {
    console.warn(`[RateLimit] IP ${ip} excedeu 5 comentários/hora`);
    return res.status(429).json({ error: 'Muitos comentários. Aguarde 1 hora.' });
  }
  const { post_id, post_slug, author, content } = req.body;
  if (!post_slug || !author || !content) {
    return res.status(400).json({ error: 'post_slug, author e content são obrigatórios' });
  }
  if (content.length > 2000) {
    return res.status(400).json({ error: 'Comentário muito longo (máx 2000 chars)' });
  }
  const result = await db.createComment({ post_id: post_id || 0, post_slug, author: stripHtml(author), content: stripHtml(content) });
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

app.get('/robots.txt', (req, res) => {
  res.setHeader('Content-Type', 'text/plain');
  res.send(`User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: ${process.env.PORTAL_URL || 'https://noticias.frotaparatodos.com.br'}/sitemap.xml`);
});

// 404 catch-all (deve ser o último middleware)
app.use((req, res) => {
  res.status(404).sendFile(path.join(__dirname, 'public', '404.html'));
});

app.listen(PORT, () => {
  console.log(`Portal FPT rodando em http://localhost:${PORT}`);
});
