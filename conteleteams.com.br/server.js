const express = require('express');
const compression = require('compression');
const path = require('path');
const crypto = require('crypto');

// ===== Enhanced Conversions helpers (growth#76) =====
function normalizeEmail(email) {
  if (!email || typeof email !== 'string') return '';
  return email.trim().toLowerCase();
}

function normalizePhoneBR(phone) {
  if (!phone || typeof phone !== 'string') return '';
  let digits = phone.replace(/\D/g, '');
  if (!digits) return '';
  if (digits.length === 12 || digits.length === 13) {
    if (digits.startsWith('55')) return '+' + digits;
  }
  if (digits.length === 10 || digits.length === 11) return '+55' + digits;
  return '+' + digits;
}

function sha256Hex(value) {
  if (!value) return null;
  return crypto.createHash('sha256').update(value).digest('hex');
}

function hashEmail(email) {
  const norm = normalizeEmail(email);
  return norm ? sha256Hex(norm) : null;
}

function hashPhoneBR(phone) {
  const norm = normalizePhoneBR(phone);
  return norm ? sha256Hex(norm) : null;
}

const app = express();
app.use(compression());
app.use(express.json());

// ===== HEALTH CHECK =====
app.get('/health', (req, res) => res.json({ ok: true, ts: new Date().toISOString() }));

// ===== REDIRECTS (WordPress legacy + SEO) =====
const REDIRECTS = {
  // Content pages (WordPress legacy → external)
  '/indique-ganhe': 'https://indique.contele.io/',
  '/indique-ganhe/': 'https://indique.contele.io/',
  // termos-uso: served as static page (termos-uso/index.html)
  '/privacidade': 'https://exclusivo.contelege.com.br/politica-privacidade/',
  '/privacidade/': 'https://exclusivo.contelege.com.br/politica-privacidade/',
  '/politica-privacidade': 'https://exclusivo.contelege.com.br/politica-privacidade/',
  '/politica-privacidade/': 'https://exclusivo.contelege.com.br/politica-privacidade/',
  '/blog': 'https://blog.contelege.com.br/?utm_source=conteleteams&utm_medium=redirect',
  '/blog/': 'https://blog.contelege.com.br/?utm_source=conteleteams&utm_medium=redirect',
  '/contato': '/#planos',
  '/contato/': '/#planos',
  '/sobre': 'https://contele.io/?utm_source=conteleteams&utm_medium=redirect',
  '/sobre/': 'https://contele.io/?utm_source=conteleteams&utm_medium=redirect',
  // Feed
  '/feed': 'https://blog.contelege.com.br/feed/',
  '/feed/': 'https://blog.contelege.com.br/feed/',
  // WordPress admin (block)
  '/wp-login.php': '/',
  '/wp-admin': '/',
  '/wp-admin/': '/',
  '/xmlrpc.php': '/',
  '/wp-json': '/',
  '/wp-json/': '/',
  '/comments/feed': '/',
  '/comments/feed/': '/',
  '/teste-formulario-v2': '/',
  '/teste-formulario-v2/': '/',
  '/wp-sitemap.xml': '/sitemap.xml',
};
app.use((req, res, next) => {
  const target = REDIRECTS[req.path];
  if (target) return res.redirect(301, target);
  next();
});

// Static files with aggressive caching
app.use(express.static(path.join(__dirname), {
  extensions: ['html'],
  maxAge: '7d',
  setHeaders: (res, filePath) => {
    // Images, SVGs: cache 30 days
    if (/\.(webp|svg|png|jpg|ico)$/i.test(filePath)) {
      res.setHeader('Cache-Control', 'public, max-age=2592000, immutable');
    }
    // HTML: no cache (always fresh)
    if (/\.html$/i.test(filePath)) {
      res.setHeader('Cache-Control', 'no-cache, must-revalidate');
    }
  }
}));

// Security headers (override Cloudflare defaults that break YouTube embeds)
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.removeHeader('X-Frame-Options');
  next();
});

// ===== CONFIG =====
const MIN_TEAM_SIZE = 4;

const PIPEDRIVE_TOKEN = process.env.PIPEDRIVE_API_TOKEN;
const EVOLUTION_URL = process.env.EVOLUTION_API_URL || 'https://evolution-api-817d7afc.contele.io';
const EVOLUTION_KEY = process.env.EVOLUTION_API_KEY;
const EVOLUTION_INSTANCE = process.env.EVOLUTION_INSTANCE || 'Vendas n2';
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK_URL;
const DISCORD_WEBHOOK = process.env.DISCORD_WEBHOOK_URL || 'https://discord.com/api/webhooks/1484533109553758208/qHY5TOheRHN_4-kJdPISRb1KgCO_UTzxy4NmL7B4gzi_0SXkyIt0gQq6olHAz5jHYnKM';
// Canal dedicado pra falhas sensiveis (lead perdido, Pipe fail, sheet fail).
// Nao mistura com notificacoes normais pra nao afogar o sinal critico.
const DISCORD_LEAD_CRITICAL_WEBHOOK = process.env.DISCORD_LEAD_CRITICAL_WEBHOOK_URL || 'https://discord.com/api/webhooks/1460216471270723769/cEq-Rc-Dzgm_GYRZpGoVWNYWEMZAYQLNPcQ1cMu1upPw4rowRmc-x8ILTAQN5M8_Hip4';
const SPREADSHEET_API = 'https://ge-prd-web-api.contele.com.br/api/v1/spreadsheet/1cM0RpSRWarWNqSYDfjqTkPnrWI1BSP8jicm77n3KiTY';
// SDR v2 cutover (28/04/2026): server.js posta direto no Leo IA em
// contele-os, sem passar pelo n8n. O fluxo antigo n8n (workflows
// Q6wWoYNqQQVqcHly + pXUbMrLyOyTIqBNr) fica desativado mas nao deletado por
// 30d como rollback. Spec: assistant-sexta-feira/docs/superpowers/specs/
// 2026-04-28-sdr-v2-teams-cutover-design.md (M5).
const SDR_WEBHOOK = process.env.SDR_WEBHOOK_URL || 'https://os.contele.io/api/webhooks/sales-lead';
const SDR_WEBHOOK_SECRET = process.env.SALES_WEBHOOK_SECRET || 'leo-vendas-2026';
const LEONARDO_PHONE = '5511999796461';

// Contele OS (fonte de verdade de tracking GA4/UTM/gclid, issue growth#77)
const CONTELE_OS_URL = process.env.CONTELE_OS_URL || 'https://os.contele.io';
const CONTELE_OS_WEBHOOK_SECRET = process.env.CONTELE_OS_WEBHOOK_SECRET || '';
if (!CONTELE_OS_WEBHOOK_SECRET) {
  console.warn('[STARTUP] WARNING: CONTELE_OS_WEBHOOK_SECRET vazio! Tracking nao sera propagado pro Contele OS.');
}

// Vendor IDs
const ID_DANIEL = 13133598;
const ID_SHEILA = 6186902;
const VENDORS = {
  [ID_SHEILA]: { nome: 'Sheila', phone: '5511973527309' },
  [ID_DANIEL]: { nome: 'Daniel', phone: '5513997431489' }
};

// Pipedrive custom field keys
const PD_FIELDS = {
  info: 'd32b1afb76380fd11b2979947d42701ca0ab1884',
  utm: 'f0fbb1341f09d81ca594898bab753004fb28b6ec',
  licencas: '3c8d91b14db8b39066af6d9ccac83bba77382582',
  origem: 'ded37a6dfbe7c85aacde82a228ac17011b97cca0',
  gclid: '51bccf176e39e275ee09ace59bc724e0eb0157ab',
  ga4: 'e98e94a65dcb60d96401853899c2126819991a43',
  chatwoot: '1fe8780223d0b482b4de80f742f6d5c261858fe8'
};

// ===== HELPERS =====
async function pipedrivePost(resource, body) {
  try {
    const res = await fetch(`https://api.pipedrive.com/v1/${resource}?api_token=${PIPEDRIVE_TOKEN}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!data.success) {
      console.error(`Pipedrive ${resource} error [${res.status}]:`, JSON.stringify(data.error).slice(0, 400));
      return { ok: false, data, error: data.error, status: res.status };
    }
    return { ok: true, data };
  } catch (err) {
    console.error(`Pipedrive ${resource} throw:`, err.message);
    return { ok: false, data: null, error: err.message, status: 0 };
  }
}

async function pipedriveGet(resource, qs = '') {
  try {
    const sep = qs ? '&' : '';
    const url = `https://api.pipedrive.com/v1/${resource}?api_token=${PIPEDRIVE_TOKEN}${sep}${qs}`;
    const res = await fetch(url);
    const data = await res.json();
    if (!data.success) {
      console.error(`Pipedrive GET ${resource} error [${res.status}]:`, JSON.stringify(data.error).slice(0, 400));
      return { ok: false, data, error: data.error, status: res.status };
    }
    return { ok: true, data };
  } catch (err) {
    console.error(`Pipedrive GET ${resource} throw:`, err.message);
    return { ok: false, data: null, error: err.message, status: 0 };
  }
}

// ===== DEDUP: busca deal aberto recente no Pipedrive antes de criar duplicado =====
// Trata o caso classico onde o lead submete o form de novo (double-click,
// reload acidental, ou retorno em outro dia) e cai 2x na pipeline. Sem esse
// gate, server.js sempre cria pessoa+deal novos, e Daniel acaba fechando
// duplicados como DUPLICADO manualmente toda semana.
//
// Estrategia: search por email (exato) e por telefone, juntar candidatos,
// pedir os deals abertos de cada pessoa, retornar o MAIS RECENTE em pipeline
// 12 (Teams) com idade < DEDUP_WINDOW_DAYS.
//
// Exact-match no Pipedrive search exige `exact_match=true` + `fields` certo.
const DEDUP_WINDOW_DAYS = 30;
const TEAMS_PIPELINE_ID = 12;

async function findExistingTeamsDeal(email, phone) {
  const qsEmail = email
    ? `term=${encodeURIComponent(email)}&fields=email&exact_match=true&limit=5`
    : null;
  const qsPhone = phone
    ? `term=${encodeURIComponent(phone)}&fields=phone&exact_match=false&limit=5`
    : null;

  const [byEmail, byPhone] = await Promise.all([
    qsEmail ? pipedriveGet('persons/search', qsEmail) : Promise.resolve({ ok: false }),
    qsPhone ? pipedriveGet('persons/search', qsPhone) : Promise.resolve({ ok: false })
  ]);

  const itemsEmail = byEmail.ok ? (byEmail.data?.data?.items || []) : [];
  const itemsPhone = byPhone.ok ? (byPhone.data?.data?.items || []) : [];
  const personIds = new Set();
  for (const it of [...itemsEmail, ...itemsPhone]) {
    const pid = it?.item?.id;
    if (pid) personIds.add(pid);
  }
  if (personIds.size === 0) return null;

  const cutoff = Date.now() - DEDUP_WINDOW_DAYS * 24 * 60 * 60 * 1000;
  let best = null; // { person_id, deal }

  for (const pid of personIds) {
    const r = await pipedriveGet(`persons/${pid}/deals`, 'status=open&limit=20');
    if (!r.ok) continue;
    const deals = r.data?.data || [];
    for (const d of deals) {
      if (d.pipeline_id !== TEAMS_PIPELINE_ID) continue;
      const addedAt = d.add_time ? new Date(d.add_time + 'Z').getTime() : 0;
      if (!addedAt || addedAt < cutoff) continue;
      if (!best || addedAt > best.addedAt) {
        best = { person_id: pid, deal: d, addedAt };
      }
    }
  }

  return best ? { person_id: best.person_id, deal: best.deal } : null;
}

async function sendWhatsApp(number, text) {
  try {
    await fetch(`${EVOLUTION_URL}/message/sendText/${encodeURIComponent(EVOLUTION_INSTANCE)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'apikey': EVOLUTION_KEY },
      body: JSON.stringify({ number, linkPreview: false, text })
    });
  } catch (err) {
    console.error('WhatsApp send error:', err.message);
  }
}

// ===== GOOGLE ADS OFFLINE CONVERSION UPLOAD =====
async function getGoogleAdsToken() {
  const resp = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.GOOGLE_ADS_CLIENT_ID,
      client_secret: process.env.GOOGLE_ADS_CLIENT_SECRET,
      refresh_token: process.env.GOOGLE_ADS_REFRESH_TOKEN,
      grant_type: 'refresh_token'
    })
  });
  const data = await resp.json();
  if (!data.access_token) {
    console.error('[GADS] Token refresh failed:', JSON.stringify(data).slice(0, 300));
  }
  return data.access_token;
}

async function uploadGoogleAdsConversion(gclid, conversionAction, conversionValue, conversionDateTime, hashedEmail, hashedPhone) {
  const token = await getGoogleAdsToken();
  if (!token) {
    const err = { error: 'no_access_token', success: false };
    await sendDiscord(`🚨 **Google Ads token refresh FAILED** | Conversions not uploading`);
    return err;
  }

  const customerId = (process.env.GOOGLE_ADS_CUSTOMER_ID || '5532904101').replace(/-/g, '');
  const devToken = process.env.GOOGLE_ADS_DEVELOPER_TOKEN || 'HMDVGk1M3N0rotf2zXiZXQ';

  const resp = await fetch(`https://googleads.googleapis.com/v23/customers/${customerId}:uploadClickConversions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'developer-token': devToken,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      conversions: [{
        gclid: gclid,
        conversionAction: conversionAction,
        conversionDateTime: conversionDateTime,
        conversionValue: conversionValue,
        currencyCode: 'BRL',
        ...(hashedEmail || hashedPhone ? {
          userIdentifiers: [
            ...(hashedEmail ? [{ hashedEmail }] : []),
            ...(hashedPhone ? [{ hashedPhoneNumber: hashedPhone }] : [])
          ]
        } : {})
      }],
      partialFailure: true
    })
  });

  const result = await resp.json();

  // Detect partialFailureError (API returns 200 but conversion failed)
  if (result.partialFailureError) {
    const errMsg = result.partialFailureError.message || 'unknown';
    const errCode = result.partialFailureError.details?.[0]?.errors?.[0]?.errorCode || {};
    console.error(`[GADS] PARTIAL FAILURE: ${errMsg}`);
    result.success = false;
    result.failureReason = Object.values(errCode)[0] || errMsg;
  } else if (result.error) {
    console.error(`[GADS] API ERROR ${result.error.code}: ${result.error.message}`);
    result.success = false;
    result.failureReason = `${result.error.status || result.error.code}: ${result.error.message}`;
  } else {
    result.success = true;
  }

  return result;
}

function brConversionDateTime() {
  // Format required by Google Ads: "2026-03-20 12:00:00-03:00"
  // Uses Intl.DateTimeFormat.formatToParts for reliable output across Node.js versions
  const now = new Date();
  const fmt = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Sao_Paulo',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
    timeZoneName: 'longOffset'
  });
  const parts = Object.fromEntries(
    fmt.formatToParts(now).map(p => [p.type, p.value])
  );
  // hour12:false can return "24" for midnight in some engines; normalize to "00"
  const hour = parts.hour === '24' ? '00' : parts.hour;
  // timeZoneName "longOffset" gives "GMT-03:00" or "GMT-3" depending on engine
  const tzRaw = parts.timeZoneName || 'GMT-03:00';
  const tzMatch = tzRaw.match(/GMT([+-]\d{1,2}(?::\d{2})?)/);
  let offset = '-03:00'; // fallback: Brazil standard time
  if (tzMatch) {
    const raw = tzMatch[1]; // e.g. "-3" or "-03:00"
    if (raw.includes(':')) {
      // Ensure hours are zero-padded: "-3:00" -> "-03:00"
      offset = raw.replace(/([+-])(\d)(:\d{2})/, '$1$20$3');
      if (offset.match(/^[+-]\d{1}$/)) offset = offset.replace(/([+-])(\d)$/, '$10$2:00');
    } else {
      // No colon: "-3" -> "-03:00"
      const n = parseInt(raw, 10);
      const sign = n >= 0 ? '+' : '-';
      offset = `${sign}${String(Math.abs(n)).padStart(2, '0')}:00`;
    }
  }
  return `${parts.year}-${parts.month}-${parts.day} ${hour}:${parts.minute}:${parts.second}${offset}`;
}

async function sendDiscord(content) {
  if (!DISCORD_WEBHOOK) return;
  try {
    await fetch(DISCORD_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
  } catch (err) {
    console.error('Discord error:', err.message);
  }
}

// Canal critico: falhas no fluxo de captura de lead (Pipe, sheet, SDR).
// Qualquer evento que signifique "lead perdido ou em risco de perder" vem aqui.
async function sendDiscordCritical(content) {
  if (!DISCORD_LEAD_CRITICAL_WEBHOOK) return;
  try {
    await fetch(DISCORD_LEAD_CRITICAL_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });
  } catch (err) {
    console.error('Discord critical error:', err.message);
  }
}

async function sendSlack(text) {
  if (!SLACK_WEBHOOK) return;
  try {
    await fetch(SLACK_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
  } catch (err) {
    console.error('Slack error:', err.message);
  }
}

async function appendSheet(data) {
  try {
    const res = await fetch(SPREADSHEET_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spreadsheetData: data })
    });
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      console.error(`Sheets error [${res.status}]:`, body.slice(0, 300));
      // Alert critico: lead pode estar no Pipe mas sumiu do relatorio
      sendDiscordCritical(
        `🚨 **appendSheet FAILED** [${res.status}]\n` +
        `Lead: ${data.Nome || '?'} | ${data.Empresa || '?'} | ${data.Telefone || '?'}\n` +
        `Status: ${data.status || '?'} | ID Pipe: ${data['ID Pipe'] || 'sem'}\n` +
        `Body: ${body.slice(0, 200)}`
      ).catch(() => {});
      return false;
    }
    return true;
  } catch (err) {
    console.error('Sheets throw:', err.message);
    sendDiscordCritical(
      `🚨 **appendSheet THROW**\n` +
      `Lead: ${data.Nome || '?'} | ${data.Empresa || '?'} | ${data.Telefone || '?'}\n` +
      `Status: ${data.status || '?'} | ID Pipe: ${data['ID Pipe'] || 'sem'}\n` +
      `Erro: ${err.message}`
    ).catch(() => {});
    return false;
  }
}

function assignVendor(tamanho) {
  // Sheila em licenca maternidade (a partir de 31/03/2026)
  // Todos os leads direcionados para Daniel
  return { id: ID_DANIEL, nome: 'Daniel' };
}

function buildUtmString(body) {
  const parts = [];
  if (body.utm_source) parts.push('utm_source=' + body.utm_source);
  if (body.utm_medium) parts.push('utm_medium=' + body.utm_medium);
  if (body.campanha) parts.push('utm_campaign=' + body.campanha);
  if (body.utm_term) parts.push('utm_term=' + body.utm_term);
  if (body.utm_content) parts.push('utm_content=' + body.utm_content);
  return parts.join('&');
}

function brDate() {
  return new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });
}

// ===== LEAD INTAKE: persistencia + trace async (incidente Pipedrive 429 25/05) =====
// Reporta o lead pro contele-os (fonte de verdade + trace por-etapa + fila de
// retry). FORA do hot path: gated por LEAD_INTAKE_ENABLED (default off),
// fire-and-forget, try/catch interno. Se o POST falhar, persiste num arquivo
// no volume Railway pra flush posterior. NUNCA pode regredir o caminho de
// sucesso do lead. Decisao claude-code-founder 26/05 (async-parallel).
const LEAD_INTAKE_ENABLED = process.env.LEAD_INTAKE_ENABLED === 'true';
const LEAD_INTAKE_URL = `${CONTELE_OS_URL}/api/webhooks/lead-intake`;

function persistIntakeFallback(payload) {
  try {
    const dir = process.env.RAILWAY_VOLUME_MOUNT_PATH || '/tmp';
    require('fs').appendFileSync(path.join(dir, 'lead-intake-unsent.jsonl'), JSON.stringify(payload) + '\n');
  } catch (err) {
    console.error('[INTAKE] fallback persist failed:', err.message);
  }
}

function reportLeadIntake(body, status, extra = {}) {
  if (!LEAD_INTAKE_ENABLED) return;
  try {
    const payload = {
      lead_intake_id: (body && body._replay && body._replay.lead_intake_id) || undefined,
      product: 'teams',
      raw_payload: body,
      name: body.nome || null,
      email: body.email || null,
      phone: body.telefone || null,
      company: body.empresa || null,
      qty: parseInt(body.tamanho_equipe, 10) || null,
      gclid: body.gclid || null,
      utm: {
        utm_source: body.utm_source || null,
        utm_medium: body.utm_medium || null,
        utm_campaign: body.campanha || null,
        utm_term: body.utm_term || null,
        utm_content: body.utm_content || null
      },
      source: body.landing_page || null,
      status,
      pipedrive_deal_id: extra.dealId || null,
      pipedrive_person_id: extra.personId || null,
      last_error: extra.error || null,
      events: extra.events || null
    };
    fetch(LEAD_INTAKE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-webhook-secret': SDR_WEBHOOK_SECRET },
      body: JSON.stringify(payload)
    }).then((r) => { if (!r.ok) persistIntakeFallback(payload); })
      .catch(() => persistIntakeFallback(payload));
  } catch (err) {
    console.error('[INTAKE] report threw:', err.message);
  }
}

// ===== LEAD ENDPOINT =====
app.post('/api/lead', async (req, res) => {
  const body = req.body;
  let tamanho = parseInt(body.tamanho_equipe, 10) || 0;

  // Normaliza telefone: garante DDI 55 quando ausente (closes #70)
  let tel = (body.telefone || '').replace(/\D/g, '');
  if (tel.length > 0 && tel.length <= 11) tel = '55' + tel;
  body.telefone = tel;

  const ctaSource = body.cta_source || 'testar';
  console.log(`[LEAD] ${body.nome} | ${body.empresa} | ${tamanho} lic | cta=${ctaSource} | gclid=${body.gclid ? 'yes' : 'no'}`);

  // Quick response to frontend (don't block)
  res.json({ ok: true });

  // Wrapper global: qualquer throw nao-tratado dispara alerta critico pra
  // nao perder lead silenciosamente. Frontend ja recebeu 200, entao processar
  // em background com guard.
  try {
  await processLead(body, tamanho, ctaSource);
  } catch (err) {
    console.error('[LEAD] Handler crashed:', err);
    await sendDiscordCritical(
      `🚨 **LEAD HANDLER CRASHED** (possivel lead perdido)\n` +
      `Lead: ${body?.nome || '?'} | ${body?.empresa || '?'} | ${body?.telefone || '?'} | ${body?.email || '?'}\n` +
      `Licencas: ${tamanho} | CTA: ${ctaSource}\n` +
      `Erro: ${err.message}\n\`\`\`${(err.stack || '').slice(0, 400)}\`\`\``
    ).catch(() => {});
  }
});

async function processLead(body, tamanho, ctaSource) {

  // Filter test submissions: log to sheet but skip Pipedrive/SDR/notifications
  const isTest = /teste|test|prova|fake/i.test(body.nome || '') ||
                 /teste|test|fake|@contele\.com/i.test(body.email || '') ||
                 /contele/i.test(body.empresa || '');
  if (isTest) {
    const sheetData = {
      'Data': brDate(), 'Nome': body.nome || '', 'Email': body.email || '',
      'Telefone': body.telefone || '', 'Empresa': body.empresa || '',
      'Campanha': body.campanha || '', 'Tamanho da Equipe': String(tamanho),
      'Landing Page': body.landing_page || '', 'status': '3-temp-can-delete-teste',
      'GCLID': body.gclid || '', 'GA4 Client ID': body.ga4_client_id || '',
      'utm_source': body.utm_source || '', 'utm_medium': body.utm_medium || '',
      'utm_term': body.utm_term || '', 'utm_content': body.utm_content || '',
      'CTA': ctaSource
    };
    await appendSheet(sheetData);
    console.log(`[LEAD] TEST FILTERED: ${body.nome} -> sheet only`);
    return;
  }

  // Build sheet data (common for all leads)
  const sheetData = {
    'Data': brDate(),
    'Nome': body.nome || '',
    'Email': body.email || '',
    'Telefone': body.telefone || '',
    'Empresa': body.empresa || '',
    'Campanha': body.campanha || '',
    'Tamanho da Equipe': String(tamanho),
    'Landing Page': body.landing_page || '',
    'GCLID': body.gclid || '',
    'GA4 Client ID': body.ga4_client_id || '',
    'utm_source': body.utm_source || '',
    'utm_medium': body.utm_medium || '',
    'utm_term': body.utm_term || '',
    'utm_content': body.utm_content || '',
    'CTA': ctaSource
  };

  // ===== LEAD INADEQUADO (< MIN_TEAM_SIZE) =====
  // small_team_accepted: lead had <4 lic but accepted min package (4 lic)
  const smallTeamAccepted = body.small_team_accepted === true;
  if (!smallTeamAccepted && (body.lead_inadequado || tamanho < MIN_TEAM_SIZE)) {
    sheetData['status'] = '4_lead_inadequado';
    await appendSheet(sheetData);
    console.log(`[LEAD] Inadequado: ${body.nome} (${tamanho} lic) -> sheet only`);
    return;
  }
  // If small_team_accepted, force tamanho to MIN_TEAM_SIZE and proceed to create deal
  if (smallTeamAccepted) {
    const originalSize = body.tamanho_equipe_original || tamanho;
    tamanho = MIN_TEAM_SIZE;
    sheetData['Tamanho da Equipe'] = `${MIN_TEAM_SIZE} (original: ${originalSize})`;
    console.log(`[LEAD] Small team accepted min package: ${body.nome} (original: ${originalSize} -> ${MIN_TEAM_SIZE} lic)`);
  }

  // ===== LEAD QUALIFICADO =====
  const vendor = assignVendor(tamanho);
  const utmString = buildUtmString(body);

  // ===== DEDUP GATE (Pipedrive-aware) =====
  // Casos cobertos:
  //  - Double-click no botao (passou pela trava client): chega 2 requests aqui
  //    em janela de segundos. A 2a vai achar o deal recem criado pela 1a.
  //  - Re-submit em outro dia (caso Rogerio Siqueira 23/04 + 29/04): pessoa
  //    ja existe no Pipe com deal aberto na pipeline 12. Nao queremos virar
  //    DUPLICADO manual pro Daniel toda semana.
  //  - Re-submit de outro browser/device: localStorage do client nao cobre,
  //    Pipedrive cobre.
  // Atualiza tracking no contele-os com o deal_id existente (pra capturar UTMs
  // novos do retorno) e sai antes de criar pessoa/deal duplicado.
  const dedup = await findExistingTeamsDeal(body.email, body.telefone);
  if (dedup) {
    const existingDealId = dedup.deal.id;
    sheetData['status'] = '6_duplicado_pipedrive';
    sheetData['Vendedor'] = VENDORS[dedup.deal.user_id?.value ?? dedup.deal.user_id]?.nome || '';
    sheetData['ID Pipe'] = String(existingDealId);
    await appendSheet(sheetData);

    // Atualiza tracking (UTMs/gclid/GA4) no deal existente via contele-os.
    // Sales-tracking webhook ja faz match por pipedrive_deal_id e patch.
    if (CONTELE_OS_WEBHOOK_SECRET) {
      fetch(`${CONTELE_OS_URL}/api/webhooks/sales-tracking`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': CONTELE_OS_WEBHOOK_SECRET
        },
        body: JSON.stringify({
          pipedrive_deal_id: existingDealId,
          email: body.email || null,
          phone: body.telefone || null,
          gclid: body.gclid || null,
          ga4_client_id: body.ga4_client_id || null,
          ga4_session_id: body.ga4_session_id || null,
          utm_source: body.utm_source || null,
          utm_medium: body.utm_medium || null,
          utm_campaign: body.campanha || null,
          utm_term: body.utm_term || null,
          utm_content: body.utm_content || null,
          landing_page: body.landing_page || null,
          hashed_email: hashEmail(body.email),
          hashed_phone: hashPhoneBR(body.telefone),
          raw_gclid: body.gclid || null
        })
      }).catch(err => {
        console.error('[DEDUP] sales-tracking refresh threw:', err.message);
      });
    }

    sendDiscord(
      `🔁 **Submit duplicado bloqueado** (Teams)\n\n` +
      `**${body.empresa || body.nome}** | ${tamanho} lic | CTA: ${ctaSource}\n` +
      `${body.email} | ${body.telefone}\n` +
      `Deal aberto existente: <https://contelegv.pipedrive.com/deal/${existingDealId}>\n` +
      `Adicionado em: ${dedup.deal.add_time} | Owner: ${VENDORS[dedup.deal.user_id?.value ?? dedup.deal.user_id]?.nome || 'desconhecido'}\n` +
      `Tracking atualizado no contele-os. Nao criamos pessoa/deal duplicado.`
    ).catch(() => {});

    reportLeadIntake(body, 'dedup_existing', {
      dealId: existingDealId,
      personId: dedup.person_id,
      events: [{ step: 'dedup', status: 'ok', metadata: { existing_deal_id: existingDealId } }]
    });
    console.log(`[LEAD] DEDUP: skipped duplicate for ${body.empresa} (${body.email}) -> existing deal=${existingDealId} person=${dedup.person_id}`);
    return;
  }

  // 1. Create Person in Pipedrive
  const personRes = await pipedrivePost('persons', {
    name: body.nome,
    email: [body.email],
    phone: [body.telefone]
  });
  const personId = personRes.ok ? personRes.data?.data?.id : null;

  if (!personRes.ok || !personId) {
    // Person nao foi criada: lead morre aqui. Nao adianta tentar Deal sem
    // person_id. Marca sheet como fail e alerta critico.
    sheetData['status'] = '5_pipedrive_person_failed';
    sheetData['Vendedor'] = '';
    sheetData['ID Pipe'] = '';
    await appendSheet(sheetData);
    await sendDiscordCritical(
      `🚨 **Pipedrive PERSON FAILED** (lead nao virou deal)\n` +
      `Lead: ${body.nome} | ${body.empresa} | ${body.telefone} | ${body.email}\n` +
      `Licencas: ${tamanho} | CTA: ${ctaSource}\n` +
      `Status: ${personRes.status} | Erro: ${JSON.stringify(personRes.error).slice(0, 200)}`
    ).catch(() => {});
    reportLeadIntake(body, 'pipedrive_failed', {
      error: `person: ${personRes.status} ${JSON.stringify(personRes.error).slice(0, 200)}`,
      events: [{ step: 'pipedrive_person', status: 'failed', http_status: personRes.status }]
    });
    console.error(`[LEAD] ABORT: person creation failed for ${body.empresa}`);
    return;
  }

  // 2. Create Deal in Pipedrive (with GCLID, GA4, UTMs)
  const dealBody = {
    title: body.empresa || body.nome,
    person_id: personId,
    stage_id: 94,
    pipeline_id: 12,
    user_id: vendor.id,
    value: tamanho,
    currency: 'BRL',
    visible_to: 3,
    status: 'open'
  };
  const ctaLabel = { testar: 'Teste Grátis', especialista: 'Falar com Especialista', contratar: 'Contratar Agora' }[ctaSource] || ctaSource;
  dealBody[PD_FIELDS.info] = smallTeamAccepted
    ? `[PACOTE MINIMO] Lead tinha ${body.tamanho_equipe_original || '?'} lic, aceitou pacote de ${MIN_TEAM_SIZE}. CTA: ${ctaLabel}. ${body.info || ''}`
    : `CTA: ${ctaLabel}. ${body.info || ''}`;
  dealBody[PD_FIELDS.utm] = utmString;
  dealBody[PD_FIELDS.licencas] = tamanho;
  dealBody[PD_FIELDS.origem] = body.landing_page || '';
  dealBody[PD_FIELDS.gclid] = body.gclid || '';
  dealBody[PD_FIELDS.ga4] = body.ga4_client_id || '';

  const dealRes = await pipedrivePost('deals', dealBody);
  const dealId = dealRes.ok ? dealRes.data?.data?.id : null;

  if (!dealRes.ok || !dealId) {
    // Deal nao foi criado: lead fica orfao (pessoa existe, deal nao). Marca
    // sheet + alerta + NAO dispara notifs pra evitar URL quebrada.
    sheetData['status'] = '5_pipedrive_deal_failed';
    sheetData['Vendedor'] = vendor.nome;
    sheetData['ID Pipe'] = '';
    await appendSheet(sheetData);
    await sendDiscordCritical(
      `🚨 **Pipedrive DEAL FAILED** (person criada mas deal nao, lead orfao)\n` +
      `Lead: ${body.nome} | ${body.empresa} | ${body.telefone} | ${body.email}\n` +
      `Licencas: ${tamanho} | CTA: ${ctaSource}\n` +
      `Person ID: ${personId}\n` +
      `Status: ${dealRes.status} | Erro: ${JSON.stringify(dealRes.error).slice(0, 200)}`
    ).catch(() => {});
    reportLeadIntake(body, 'pipedrive_failed', {
      personId,
      error: `deal: ${dealRes.status} ${JSON.stringify(dealRes.error).slice(0, 200)}`,
      events: [
        { step: 'pipedrive_person', status: 'ok' },
        { step: 'pipedrive_deal', status: 'failed', http_status: dealRes.status }
      ]
    });
    console.error(`[LEAD] ABORT: deal creation failed for ${body.empresa} (person=${personId})`);
    return;
  }

  console.log(`[LEAD] Pipedrive: person=${personId} deal=${dealId} vendor=${vendor.nome}`);

  // 2b. Propaga tracking completo pro Contele OS (fire-and-forget, nao bloqueia).
  // Issue growth#77: ga4_session_id precisa chegar no webhook Pipedrive depois
  // pra fechar attribution session-scoped no GA4 MP. Custom field Pipedrive
  // `ga4` (client_id) continua populado acima como fallback.
  if (CONTELE_OS_WEBHOOK_SECRET) {
    fetch(`${CONTELE_OS_URL}/api/webhooks/sales-tracking`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-webhook-secret': CONTELE_OS_WEBHOOK_SECRET
      },
      body: JSON.stringify({
        pipedrive_deal_id: dealId,
        email: body.email,
        phone: body.telefone,
        gclid: body.gclid || null,
        ga4_client_id: body.ga4_client_id || null,
        ga4_session_id: body.ga4_session_id || null,
        utm_source: body.utm_source || '',
        utm_medium: body.utm_medium || '',
        utm_campaign: body.campanha || '',
        utm_term: body.utm_term || '',
        utm_content: body.utm_content || '',
        landing_page: body.landing_page || '',
        hashed_email: hashEmail(body.email),
        hashed_phone: hashPhoneBR(body.telefone),
        raw_gclid: body.gclid || null
      })
    }).then(async (r) => {
      if (!r.ok) {
        const txt = await r.text().catch(() => '');
        console.error(`[TRACKING] Contele OS sales-tracking NON-OK [${r.status}]:`, txt.slice(0, 200));
      } else {
        console.log(`[TRACKING] Contele OS sales-tracking OK deal=${dealId} sid=${body.ga4_session_id ? 'yes' : 'no'}`);
      }
    }).catch(err => {
      console.error('[TRACKING] Contele OS sales-tracking THROW:', err.message);
    });
  } else {
    console.warn(`[TRACKING] Skipping Contele OS propagation (secret empty) deal=${dealId}`);
  }

  // 3. Update sheet data with deal info
  sheetData['status'] = smallTeamAccepted ? '2-small-team-accepted-deal-created' : '1-success-deal-created-in-pipedrive';
  sheetData['Vendedor'] = vendor.nome;
  sheetData['ID Pipe'] = String(dealId);

  // 4. Run remaining tasks in parallel
  const pipedriveUrl = `https://contelegv.pipedrive.com/deal/${dealId}`;
  const waLink = `https://wa.me/${body.telefone}`;
  const faixa = tamanho >= 21 ? 'Grande (21+)' : tamanho >= 10 ? 'Media (10-20)' : 'Pequena (4-9)';

  const notifText = [
    `Novo lead Teams!`,
    ``,
    `${body.empresa} | ${tamanho} usuarios | ${faixa}`,
    `${body.nome} | ${body.telefone}`,
    `${body.email}`,
    ``,
    `Vendedor: ${vendor.nome}`,
    `CTA: ${ctaLabel}`,
    `Campanha: ${body.campanha || 'organico'}`,
    body.utm_source ? `Origem: ${body.utm_source}/${body.utm_medium || ''}` : '',
    body.gclid ? `GCLID: sim (Google Ads)` : 'GCLID: nao (organico)',
    ``,
    `Pipedrive: ${pipedriveUrl}`,
    `WhatsApp: ${waLink}`
  ].filter(Boolean).join('\n');

  const slackText = [
    `:rocket: *Novo lead Teams!*`,
    ``,
    `>*${body.empresa}* | ${tamanho} usuarios | ${faixa}`,
    `>:bust_in_silhouette: ${body.nome}`,
    `>:phone: <${waLink}|${body.telefone}>`,
    `>:email: ${body.email}`,
    ``,
    `:dart: *Vendedor:* ${vendor.nome}`,
    `:bar_chart: *Campanha:* ${body.campanha || 'organico'}`,
    body.utm_source ? `:globe_with_meridians: *Origem:* ${body.utm_source}/${body.utm_medium || ''}` : null,
    body.gclid ? `:white_check_mark: *GCLID:* capturado (Google Ads)` : `:large_orange_circle: *GCLID:* sem (organico)`,
    body.utm_term ? `:mag: *Keyword:* ${body.utm_term}` : null,
    ``,
    `:link: <${pipedriveUrl}|Abrir no Pipedrive>`
  ].filter(Boolean).join('\n');

  // Replay do cron de retry com atraso >2h: nao redispara Leo (lead frio).
  const replaySkipLeo = !!(body._replay && body._replay.skip_leo === true);

  await Promise.allSettled([
    // Sheet
    appendSheet(sheetData),
    // Slack
    sendSlack(slackText),
    // WhatsApp vendedor
    sendWhatsApp(VENDORS[vendor.id]?.phone, notifText),
    // WhatsApp Leonardo
    sendWhatsApp(LEONARDO_PHONE, notifText),
    // SDR v2 (cutover 28/04/2026): post direto no Leo IA em contele-os.
    // Header x-webhook-secret obrigatorio (auth do endpoint).
    replaySkipLeo ? Promise.resolve('leo_skipped_stale') : fetch(SDR_WEBHOOK, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-webhook-secret': SDR_WEBHOOK_SECRET
      },
      body: JSON.stringify({
        nome: body.nome,
        whatsapp: body.telefone,
        email: body.email,
        pipedrive_id: dealId,
        licencas: tamanho,
        empresa: body.empresa,
        idUsuarioPipedrive: vendor.id,
        vendedor: vendor.nome,
        info: body.info || '',
        cta_source: ctaSource
      })
    }).then(async (sdrRes) => {
      // SDR webhook (n8n -> contele-os sales-lead): trigger do Leo IA.
      // Se falhar, lead existe no Pipe mas Leo nao dispara first-contact.
      if (!sdrRes.ok) {
        const txt = await sdrRes.text().catch(() => '');
        console.error(`SDR webhook non-OK [${sdrRes.status}]:`, txt.slice(0, 200));
        sendDiscordCritical(
          `🚨 **SDR webhook NON-OK** [${sdrRes.status}] (Leo IA pode nao ter disparado)\n` +
          `Lead: ${body.nome} | ${body.empresa} | ${body.telefone}\n` +
          `Deal: ${dealId} | Licencas: ${tamanho}\n` +
          `Body: ${txt.slice(0, 200)}`
        ).catch(() => {});
      }
    }).catch(err => {
      console.error('SDR webhook error:', err.message);
      sendDiscordCritical(
        `🚨 **SDR webhook THROW** (Leo IA nao disparou)\n` +
        `Lead: ${body.nome} | ${body.empresa} | ${body.telefone}\n` +
        `Deal: ${dealId} | Licencas: ${tamanho}\n` +
        `Erro: ${err.message}`
      ).catch(() => {});
    })
  ]);

  // Discord notify (Momento 1: lead novo entrou). Fire-and-forget, nao bloqueia response.
  sendDiscord(
    `🆕 **Novo lead Teams**\n\n` +
    `**${body.empresa}** • ${tamanho} licenças\n` +
    `Lead: ${body.nome}\n` +
    `Contato: ${body.email} | ${body.telefone}\n` +
    `Fonte: ${body.gclid ? 'Google Ads (GCLID ✓)' : 'orgânico'} | UTM: ${body.utm_source || '-'}/${body.utm_medium || '-'}\n` +
    `CTA: ${ctaLabel || ctaSource} | Vendor: ${vendor.nome}\n` +
    `Pipedrive: <https://contelegv.pipedrive.com/deal/${dealId}>`
  ).catch(() => {});

  reportLeadIntake(body, 'deal_created', {
    dealId,
    personId,
    events: [
      { step: 'pipedrive_deal', status: 'ok' },
      replaySkipLeo
        ? { step: 'leo_ia', status: 'skipped', metadata: { reason: 'stale_lead_>2h' } }
        : { step: 'leo_ia', status: 'ok' }
    ]
  });

  console.log(`[LEAD] Complete: ${body.empresa} -> deal ${dealId}, vendor ${vendor.nome}`);
}

// ===== PIPEDRIVE WEBHOOK: Deal Stage Change =====
// Receives Pipedrive webhook when deal changes stage
// Sends offline conversion to Google Ads (GCLID) and GA4

const GOOGLE_ADS_CONVERSION_URL = 'https://www.google-analytics.com/mp/collect';
const GA4_MEASUREMENT_ID = process.env.GA4_MEASUREMENT_ID || 'G-5VY7G6X0DJ';
const GA4_API_SECRET = process.env.GA4_API_SECRET || '';

// Pipeline 12 (Teams) stages that count as "qualified"
const QUALIFIED_STAGES = [
  96,   // APRES. REALIZADA
  209,  // ACOMPANHAMENTO DE TESTE
  245,  // AGUARDANDO APROVAÇÃO
  95,   // FECHAMENTO SEMANA
  156,  // COMPRA ATÉ 90d
];

// Onboarding/active stages (won)
const WON_STAGES = [257, 272, 278, 279, 280, 238]; // ETAPA 1-5 + BASE GE

// Dedup: persist fired conversions to Railway volume (survives redeploys)
const fs = require('fs');
const DEDUP_DIR = process.env.RAILWAY_VOLUME_MOUNT_PATH || '/tmp';
const DEDUP_FILE = path.join(DEDUP_DIR, 'fired-conversions.json');

function loadDedup() {
  try {
    const data = JSON.parse(fs.readFileSync(DEDUP_FILE, 'utf8'));
    return {
      qualified: new Set(data.qualified || []),
      won: new Set(data.won || [])
    };
  } catch {
    return { qualified: new Set(), won: new Set() };
  }
}

function saveDedup() {
  try {
    fs.writeFileSync(DEDUP_FILE, JSON.stringify({
      qualified: [...firedQualified],
      won: [...firedWon]
    }));
  } catch (err) {
    console.error('[DEDUP] Save error:', err.message);
  }
}

const { qualified: firedQualified, won: firedWon } = loadDedup();
console.log(`[DEDUP] Loaded: ${firedQualified.size} qualified, ${firedWon.size} won`);

// Startup health checks
if (!GA4_API_SECRET) console.warn('[STARTUP] WARNING: GA4_API_SECRET is empty! GA4 Measurement Protocol events will NOT be sent.');
if (!SLACK_WEBHOOK) console.warn('[STARTUP] WARNING: SLACK_WEBHOOK_URL is empty! Slack notifications disabled.');
if (!process.env.GOOGLE_ADS_CLIENT_ID) console.warn('[STARTUP] WARNING: GOOGLE_ADS_CLIENT_ID missing! Google Ads conversions will fail.');

app.post('/api/pipedrive-webhook', async (req, res) => {
  res.json({ ok: true });

  try {
  // DELETE EVENT: Pipedrive v2 sends meta.action="delete" / v1 sends event="deleted.deal".
  // Header `x-event-action` = "deleted" tambem indica delete (v1).
  // Encaminhar pro contele-os pra marcar lead como deletado (issue contele/growth#113).
  const metaAction = req.body?.meta?.action;
  const eventStr = req.body?.event;
  const headerAction = req.headers?.['x-event-action'];
  const isDelete = metaAction === 'delete' || metaAction === 'deleted'
    || eventStr === 'deleted.deal'
    || headerAction === 'deleted' || headerAction === 'delete';

  if (isDelete) {
    const prev = req.body.previous || {};
    const meta = req.body.meta || {};
    const dealId = prev.id || meta.id || req.body?.data?.id;
    const pipelineId = parseInt(prev.pipeline_id ?? meta.pipeline_id, 10);

    if (!dealId) {
      console.warn('[PIPE-DELETE] no deal_id em delete event:', JSON.stringify(req.body).slice(0, 400));
      return;
    }

    // Pipeline 12 = Teams. Outros pipelines: ignorar (cada server cuida do seu).
    if (pipelineId && pipelineId !== 12) {
      console.log(`[PIPE-DELETE] ignorando deal=${dealId} pipeline=${pipelineId} (nao-Teams)`);
      return;
    }

    console.log(`[PIPE-DELETE] forward deal=${dealId} pipeline=${pipelineId || 'n/a'} -> contele-os`);

    if (CONTELE_OS_WEBHOOK_SECRET) {
      const deletedAt = new Date().toISOString();
      fetch(`${CONTELE_OS_URL}/api/webhooks/sales-lead-delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-webhook-secret': CONTELE_OS_WEBHOOK_SECRET
        },
        body: JSON.stringify({ pipedrive_deal_id: dealId, deleted_at: deletedAt })
      })
        .then(r => console.log(`[PIPE-DELETE] OS resp ${r.status} deal=${dealId}`))
        .catch(err => console.error(`[PIPE-DELETE] OS dispatch fail deal=${dealId}:`, err.message));
    } else {
      console.warn(`[PIPE-DELETE] CONTELE_OS_WEBHOOK_SECRET vazio, skip dispatch deal=${dealId}`);
    }

    if (DISCORD_WEBHOOK) {
      fetch(DISCORD_WEBHOOK, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: `🗑️ Pipedrive delete (Teams): deal=${dealId} -> contele-os/sales-lead-delete`
        })
      }).catch(() => {});
    }

    return;
  }

  // Pipedrive v2 webhook sends "data" (not "current") and custom_fields as {type, value} objects
  const current = req.body.data || req.body.current || {};
  const previous = req.body.previous || {};
  if (!current.id) return;

  const dealId = current.id;
  const newStageId = parseInt(current.stage_id, 10);
  const oldStageId = parseInt(previous?.stage_id, 10) || 0;
  const pipelineId = parseInt(current.pipeline_id, 10);
  const status = current.status;

  console.log(`[PIPE] Received: deal=${dealId} pipeline=${pipelineId} stage=${oldStageId}->${newStageId} status=${status}`);

  // Only process Pipeline 12 (Teams)
  if (pipelineId !== 12) return;

  // CRITICAL: only process if stage actually changed OR status changed to won
  // previous may not have stage_id or status if only other fields changed
  const prevStatus = previous?.status;
  const prevStageExists = previous?.stage_id !== undefined && previous?.stage_id !== null;
  const stageChanged = prevStageExists && oldStageId !== newStageId;
  // Status changed to won ONLY if previous explicitly had a different status
  const statusChangedToWon = status === 'won' && prevStatus !== undefined && prevStatus !== 'won';

  if (!stageChanged && !statusChangedToWon) {
    console.log(`[PIPE] Ignoring: deal=${dealId} no stage change (prev_stage=${prevStageExists ? oldStageId : 'N/A'}->${newStageId}) no won change (prev_status=${prevStatus || 'N/A'})`);
    return;
  }

  // Extract custom field values (Pipedrive sends {type, value} objects in custom_fields)
  function getCustomField(fieldKey) {
    // Try custom_fields object first (v2 format)
    const cf = current.custom_fields?.[fieldKey];
    if (cf && typeof cf === 'object') return cf.value || '';
    if (cf) return cf;
    // Fallback: direct field on current (v1 format)
    return current[fieldKey] || '';
  }

  const gclidFromPipe = getCustomField(PD_FIELDS.gclid);
  const ga4ClientIdFromPipe = getCustomField(PD_FIELDS.ga4);
  const utmRaw = getCustomField(PD_FIELDS.utm);
  const dealValue = current.value || 0;
  const dealTitle = current.title || '';

  // Parse UTM string from Pipedrive (format: "utm_source=google&utm_medium=cpc&...")
  const utmParamsFromPipe = Object.fromEntries(new URLSearchParams(utmRaw));

  // Lookup tracking no Contele OS (fonte de verdade, issue growth#77).
  // Fallback: custom fields Pipedrive (ga4 client_id, gclid, utm string)
  // pra nao quebrar conversoes em andamento se Contele OS falhar.
  let ga4SessionId = '';
  let gclid = gclidFromPipe;
  let ga4ClientId = ga4ClientIdFromPipe;
  let utmSource = utmParamsFromPipe.utm_source || 'direct';
  let utmMedium = utmParamsFromPipe.utm_medium || 'none';
  let utmCampaign = utmParamsFromPipe.utm_campaign || '';
  let hashedEmail = null;
  let hashedPhone = null;

  if (CONTELE_OS_WEBHOOK_SECRET) {
    try {
      const lookup = await fetch(`${CONTELE_OS_URL}/api/webhooks/sales-tracking?deal_id=${dealId}`, {
        headers: { 'x-webhook-secret': CONTELE_OS_WEBHOOK_SECRET }
      });
      if (lookup.ok) {
        const j = await lookup.json().catch(() => ({}));
        if (j && j.found) {
          // Contele OS vence: sobrescreve campos que vieram preenchidos.
          if (j.gclid) gclid = j.gclid;
          if (j.ga4_client_id) ga4ClientId = j.ga4_client_id;
          if (j.ga4_session_id) ga4SessionId = j.ga4_session_id;
          if (j.utm_data && typeof j.utm_data === 'object') {
            if (j.utm_data.utm_source) utmSource = j.utm_data.utm_source;
            if (j.utm_data.utm_medium) utmMedium = j.utm_data.utm_medium;
            if (j.utm_data.utm_campaign) utmCampaign = j.utm_data.utm_campaign;
          }
          hashedEmail = j.hashed_email || (j.email ? hashEmail(j.email) : null);
          hashedPhone = j.hashed_phone || (j.phone ? hashPhoneBR(j.phone) : null);
          console.log(`[PIPE] Tracking do Contele OS: deal=${dealId} sid=${ga4SessionId ? 'yes' : 'no'} cid=${ga4ClientId ? 'yes' : 'no'} ec=${hashedEmail ? 'yes' : 'no'}`);
        } else {
          console.log(`[PIPE] Contele OS lookup: deal=${dealId} not_found, usando fallback Pipedrive`);
        }
      } else {
        console.warn(`[PIPE] Contele OS lookup NON-OK [${lookup.status}] deal=${dealId}, usando fallback Pipedrive`);
      }
    } catch (err) {
      console.error(`[PIPE] Contele OS lookup THROW deal=${dealId}:`, err.message);
    }
  }

  console.log(`[PIPE] Deal ${dealId} "${dealTitle}" | gclid=${gclid ? 'yes' : 'no'} | ga4_cid=${ga4ClientId ? 'yes' : 'no'} | ga4_sid=${ga4SessionId ? 'yes' : 'no'}`);

  // QUALIFIED: deal entered a qualified stage (fire only once per deal)
  if (QUALIFIED_STAGES.includes(newStageId) && !QUALIFIED_STAGES.includes(oldStageId) && !firedQualified.has(dealId)) {
    firedQualified.add(dealId); saveDedup();
    console.log(`[PIPE] QUALIFIED: ${dealTitle} (deal ${dealId}) | GCLID: ${gclid}`);

    // Send to GA4 Measurement Protocol
    let ga4Status = 'skipped';
    if (!GA4_API_SECRET) {
      console.warn(`[PIPE] GA4_API_SECRET is empty! GA4 events NOT being sent for deal ${dealId}`);
      ga4Status = 'FAILED (no API secret)';
    } else if (ga4ClientId) {
      try {
        // Params GA4 oficiais pra traffic source: `campaign_source`, `campaign_medium`,
        // `campaign_name`. `source`/`medium`/`campaign` (nomes que usavamos antes)
        // nao sao reconhecidos e resultavam em sessionSource=(not set) em 100%.
        // `engagement_time_msec: 1` evita que GA4 trate evento como "nao engajado".
        // Nota: `campaign_details` (evento auxiliar) e reservado pra Firebase/Apps
        // e e descartado em web property - nao usamos.
        // Session-scoped attribution (sessionSource preenchido em reports padrao)
        // requer `session_id` - fase 2, exige captura client-side.
        const ga4Resp = await fetch(`${GOOGLE_ADS_CONVERSION_URL}?measurement_id=${GA4_MEASUREMENT_ID}&api_secret=${GA4_API_SECRET}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            client_id: ga4ClientId,
            ...(hashedEmail || hashedPhone ? {
              user_data: {
                ...(hashedEmail ? { sha256_email_address: hashedEmail } : {}),
                ...(hashedPhone ? { sha256_phone_number: hashedPhone } : {})
              }
            } : {}),
            events: [{
              name: 'lead_qualificado',
              params: {
                value: 1,
                currency: 'BRL',
                deal_id: String(dealId),
                campaign_source: utmSource,
                campaign_medium: utmMedium,
                campaign_name: utmCampaign,
                engagement_time_msec: 1,
                ...(ga4SessionId ? { session_id: ga4SessionId } : {})
              }
            }]
          })
        });
        if (ga4Resp.status >= 200 && ga4Resp.status < 300) {
          ga4Status = 'sent';
          console.log(`[PIPE] GA4 lead_qualificado sent for deal ${dealId} (HTTP ${ga4Resp.status})`);
        } else {
          ga4Status = `FAILED (HTTP ${ga4Resp.status})`;
          console.error(`[PIPE] GA4 lead_qualificado FAILED for deal ${dealId}: HTTP ${ga4Resp.status}`);
        }
      } catch (err) {
        ga4Status = `FAILED (${err.message})`;
        console.error('[PIPE] GA4 error:', err.message);
      }
    } else {
      ga4Status = 'skipped (no client ID)';
    }

    // Upload to Google Ads (only if GCLID is complete, >= 80 chars)
    let gadsStatus = 'skipped (no full GCLID)';
    if (gclid && gclid.length >= 80) {
      try {
        const adsResult = await uploadGoogleAdsConversion(
          gclid,
          'customers/5532904101/conversionActions/7453590632',
          1.0,
          brConversionDateTime(),
          hashedEmail,
          hashedPhone
        );
        if (adsResult.success) {
          gadsStatus = 'SUCCESS';
          console.log(`[PIPE] Google Ads upload SUCCESS (qualified) deal=${dealId}`);
        } else {
          gadsStatus = `FAILED: ${adsResult.failureReason || 'unknown'}`;
          console.error(`[PIPE] Google Ads upload FAILED (qualified) deal=${dealId}: ${adsResult.failureReason}`);
          await sendDiscord(`🚨 **Google Ads upload FAILED** (lead_qualificado) deal=${dealId}\nReason: ${adsResult.failureReason}\nGCLID: ${gclid.slice(0, 30)}...`);
        }
      } catch (err) {
        gadsStatus = `ERROR: ${err.message}`;
        console.error(`[PIPE] Google Ads upload error (qualified) deal=${dealId}:`, err.message);
        await sendDiscord(`🚨 **Google Ads upload ERROR** (lead_qualificado) deal=${dealId}: ${err.message}`);
      }
    }

    // Notify Slack + Discord with real status
    await sendSlack(`:star: *Lead qualificado!*\n\n*${dealTitle}* entrou em etapa avançada\nGCLID: ${gclid ? 'sim' : 'nao'}\nGoogle Ads: ${gadsStatus}\nGA4: ${ga4Status}\n<https://contelegv.pipedrive.com/deal/${dealId}|Abrir no Pipedrive>`);
    await sendDiscord(`⭐ **Lead qualificado!**\n\n**${dealTitle}** entrou em etapa avançada\nGCLID: ${gclid || 'N/A'}\nGA4 Client ID: ${ga4ClientId || 'N/A'}\nGA4: ${ga4Status}\nGoogle Ads: ${gadsStatus}\nPipedrive: <https://contelegv.pipedrive.com/deal/${dealId}>`);
  }

  // WON: deal closed as won (fire only once per deal)
  if ((statusChangedToWon || (WON_STAGES.includes(newStageId) && !WON_STAGES.includes(oldStageId))) && !firedWon.has(dealId)) {
    firedWon.add(dealId); saveDedup();
    console.log(`[PIPE] WON: ${dealTitle} (deal ${dealId}) | value: ${dealValue} | GCLID: ${gclid}`);

    // Send to GA4 Measurement Protocol
    let ga4WonStatus = 'skipped';
    if (!GA4_API_SECRET) {
      console.warn(`[PIPE] GA4_API_SECRET is empty! GA4 events NOT being sent for deal ${dealId}`);
      ga4WonStatus = 'FAILED (no API secret)';
    } else if (ga4ClientId) {
      try {
        // Mesma correcao do lead_qualificado: params oficiais GA4.
        // Ver comentario em ~linha 720 pra contexto completo.
        const ga4Resp = await fetch(`${GOOGLE_ADS_CONVERSION_URL}?measurement_id=${GA4_MEASUREMENT_ID}&api_secret=${GA4_API_SECRET}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            client_id: ga4ClientId,
            ...(hashedEmail || hashedPhone ? {
              user_data: {
                ...(hashedEmail ? { sha256_email_address: hashedEmail } : {}),
                ...(hashedPhone ? { sha256_phone_number: hashedPhone } : {})
              }
            } : {}),
            events: [{
              name: 'lead_convertido',
              params: {
                value: dealValue,
                currency: 'BRL',
                deal_id: String(dealId),
                campaign_source: utmSource,
                campaign_medium: utmMedium,
                campaign_name: utmCampaign,
                engagement_time_msec: 1,
                ...(ga4SessionId ? { session_id: ga4SessionId } : {})
              }
            }]
          })
        });
        if (ga4Resp.status >= 200 && ga4Resp.status < 300) {
          ga4WonStatus = 'sent';
          console.log(`[PIPE] GA4 lead_convertido sent for deal ${dealId}, value ${dealValue} (HTTP ${ga4Resp.status})`);
        } else {
          ga4WonStatus = `FAILED (HTTP ${ga4Resp.status})`;
          console.error(`[PIPE] GA4 lead_convertido FAILED for deal ${dealId}: HTTP ${ga4Resp.status}`);
        }
      } catch (err) {
        ga4WonStatus = `FAILED (${err.message})`;
        console.error('[PIPE] GA4 error:', err.message);
      }
    } else {
      ga4WonStatus = 'skipped (no client ID)';
    }

    // Upload to Google Ads (only if GCLID is complete, >= 80 chars)
    let gadsWonStatus = 'skipped (no full GCLID)';
    if (gclid && gclid.length >= 80) {
      try {
        const adsResult = await uploadGoogleAdsConversion(
          gclid,
          'customers/5532904101/conversionActions/7453627859',
          dealValue || 1.0,
          brConversionDateTime(),
          hashedEmail,
          hashedPhone
        );
        if (adsResult.success) {
          gadsWonStatus = 'SUCCESS';
          console.log(`[PIPE] Google Ads upload SUCCESS (won) deal=${dealId}, value ${dealValue}`);
        } else {
          gadsWonStatus = `FAILED: ${adsResult.failureReason || 'unknown'}`;
          console.error(`[PIPE] Google Ads upload FAILED (won) deal=${dealId}: ${adsResult.failureReason}`);
          await sendDiscord(`🚨 **Google Ads upload FAILED** (lead_convertido) deal=${dealId} value=${dealValue}\nReason: ${adsResult.failureReason}\nGCLID: ${gclid.slice(0, 30)}...`);
        }
      } catch (err) {
        gadsWonStatus = `ERROR: ${err.message}`;
        console.error(`[PIPE] Google Ads upload error (won) deal=${dealId}:`, err.message);
        await sendDiscord(`🚨 **Google Ads upload ERROR** (lead_convertido) deal=${dealId}: ${err.message}`);
      }
    }

    // Notify Slack + Discord with real status
    await sendSlack(`:tada: *Deal ganho!*\n\n*${dealTitle}* virou cliente\nValor: ${dealValue} licenças\nGCLID: ${gclid ? 'sim' : 'nao'}\nGoogle Ads: ${gadsWonStatus}\nGA4: ${ga4WonStatus}\n<https://contelegv.pipedrive.com/deal/${dealId}|Abrir no Pipedrive>`);
    await sendDiscord(`🎉 **Deal ganho!**\n\n**${dealTitle}** virou cliente\nValor: ${dealValue} licenças\nGCLID: ${gclid || 'N/A'}\nGA4 Client ID: ${ga4ClientId || 'N/A'}\nGA4: ${ga4WonStatus}\nGoogle Ads: ${gadsWonStatus}\nPipedrive: <https://contelegv.pipedrive.com/deal/${dealId}>`);
  }

  } catch (err) {
    console.error('[PIPE] FATAL ERROR:', err.message, err.stack);
    await sendDiscord(`🚨 **ERRO no webhook Pipedrive!**\n\n\`\`\`${err.message}\n${err.stack?.slice(0, 300)}\`\`\`\n\nPayload keys: ${Object.keys(req.body || {}).join(', ')}\nDeal ID: ${req.body?.data?.id || req.body?.current?.id || '?'}`).catch(() => {});
    await sendSlack(`:rotating_light: *ERRO webhook Pipedrive:* ${err.message}\nDeal: ${req.body?.data?.id || '?'}`).catch(() => {});
  }
});

// ===== SPA FALLBACK =====
app.get('*', (req, res) => {
  const filePath = path.join(__dirname, req.path, 'index.html');
  res.sendFile(filePath, err => {
    if (err) res.sendFile(path.join(__dirname, 'index.html'));
  });
});

// ===== START =====
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`ConTele Teams landing running on :${PORT}`));
