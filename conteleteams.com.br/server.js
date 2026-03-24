const express = require('express');
const compression = require('compression');
const path = require('path');

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
const SPREADSHEET_API = 'https://ge-prd-web-api.contele.com.br/api/v1/spreadsheet/1cM0RpSRWarWNqSYDfjqTkPnrWI1BSP8jicm77n3KiTY';
const SDR_WEBHOOK = process.env.SDR_WEBHOOK_URL || 'https://marcofassa.app.n8n.cloud/webhook/inicio-sdr-teams-v2';
const LEONARDO_PHONE = '5511999796461';

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
  const res = await fetch(`https://api.pipedrive.com/v1/${resource}?api_token=${PIPEDRIVE_TOKEN}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (!data.success) console.error(`Pipedrive ${resource} error:`, data.error);
  return data;
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

async function uploadGoogleAdsConversion(gclid, conversionAction, conversionValue, conversionDateTime) {
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
        currencyCode: 'BRL'
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
    await fetch(SPREADSHEET_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spreadsheetData: data })
    });
  } catch (err) {
    console.error('Sheets error:', err.message);
  }
}

function assignVendor(tamanho) {
  if (tamanho >= 21) return { id: ID_SHEILA, nome: 'Sheila' };
  if (tamanho >= 10) {
    // Round-robin por segundo
    return (Math.floor(Date.now() / 1000) % 2 === 0)
      ? { id: ID_SHEILA, nome: 'Sheila' }
      : { id: ID_DANIEL, nome: 'Daniel' };
  }
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

// ===== LEAD ENDPOINT =====
app.post('/api/lead', async (req, res) => {
  const body = req.body;
  const tamanho = parseInt(body.tamanho_equipe, 10) || 0;

  console.log(`[LEAD] ${body.nome} | ${body.empresa} | ${tamanho} lic | gclid=${body.gclid ? 'yes' : 'no'}`);

  // Quick response to frontend (don't block)
  res.json({ ok: true });

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
      'utm_term': body.utm_term || '', 'utm_content': body.utm_content || ''
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
    'utm_content': body.utm_content || ''
  };

  // ===== LEAD INADEQUADO (< MIN_TEAM_SIZE) =====
  if (body.lead_inadequado || tamanho < MIN_TEAM_SIZE) {
    sheetData['status'] = '4_lead_inadequado';
    await appendSheet(sheetData);
    console.log(`[LEAD] Inadequado: ${body.nome} (${tamanho} lic) -> sheet only`);
    return;
  }

  // ===== LEAD QUALIFICADO =====
  const vendor = assignVendor(tamanho);
  const utmString = buildUtmString(body);

  // 1. Create Person in Pipedrive
  const personRes = await pipedrivePost('persons', {
    name: body.nome,
    email: [body.email],
    phone: [body.telefone]
  });
  const personId = personRes.data?.id;

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
  dealBody[PD_FIELDS.info] = body.info || '';
  dealBody[PD_FIELDS.utm] = utmString;
  dealBody[PD_FIELDS.licencas] = tamanho;
  dealBody[PD_FIELDS.origem] = body.landing_page || '';
  dealBody[PD_FIELDS.gclid] = body.gclid || '';
  dealBody[PD_FIELDS.ga4] = body.ga4_client_id || '';

  const dealRes = await pipedrivePost('deals', dealBody);
  const dealId = dealRes.data?.id;

  console.log(`[LEAD] Pipedrive: person=${personId} deal=${dealId} vendor=${vendor.nome}`);

  // 3. Update sheet data with deal info
  sheetData['status'] = '1-success-deal-created-in-pipedrive';
  sheetData['Vendedor'] = vendor.nome;
  sheetData['ID Pipe'] = String(dealId || '');

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

  await Promise.allSettled([
    // Sheet
    appendSheet(sheetData),
    // Slack
    sendSlack(slackText),
    // WhatsApp vendedor
    sendWhatsApp(VENDORS[vendor.id]?.phone, notifText),
    // WhatsApp Leonardo
    sendWhatsApp(LEONARDO_PHONE, notifText),
    // SDR (n8n Cloud: first WhatsApp message to lead)
    fetch(SDR_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        nome: body.nome,
        whatsapp: body.telefone,
        email: body.email,
        pipedrive_id: dealId,
        licencas: tamanho,
        empresa: body.empresa,
        idUsuarioPipedrive: vendor.id,
        vendedor: vendor.nome,
        info: body.info || ''
      })
    }).catch(err => {
      console.error('SDR webhook error:', err.message);
      sendDiscord(`🚨 **SDR webhook FAILED** deal=${dealId} ${body.empresa}: ${err.message}`).catch(() => {});
    })
  ]);

  console.log(`[LEAD] Complete: ${body.empresa} -> deal ${dealId}, vendor ${vendor.nome}`);
});

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

  const gclid = getCustomField(PD_FIELDS.gclid);
  const ga4ClientId = getCustomField(PD_FIELDS.ga4);
  const dealValue = current.value || 0;
  const dealTitle = current.title || '';

  console.log(`[PIPE] Deal ${dealId} "${dealTitle}" | gclid=${gclid ? 'yes' : 'no'} | ga4=${ga4ClientId ? 'yes' : 'no'}`);

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
        const ga4Resp = await fetch(`${GOOGLE_ADS_CONVERSION_URL}?measurement_id=${GA4_MEASUREMENT_ID}&api_secret=${GA4_API_SECRET}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            client_id: ga4ClientId,
            events: [{
              name: 'lead_qualificado',
              params: { value: 1, currency: 'BRL', deal_id: String(dealId) }
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
          brConversionDateTime()
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
        const ga4Resp = await fetch(`${GOOGLE_ADS_CONVERSION_URL}?measurement_id=${GA4_MEASUREMENT_ID}&api_secret=${GA4_API_SECRET}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            client_id: ga4ClientId,
            events: [{
              name: 'lead_convertido',
              params: { value: dealValue, currency: 'BRL', deal_id: String(dealId) }
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
          brConversionDateTime()
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
