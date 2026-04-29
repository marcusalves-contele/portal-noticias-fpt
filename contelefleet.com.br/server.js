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
// Copiado do Teams e adaptado pra Fleet (utm_source=contelefleet).
const REDIRECTS = {
  // Content pages (WordPress legacy -> external)
  '/indique-ganhe': 'https://indique.contele.io/',
  '/indique-ganhe/': 'https://indique.contele.io/',
  // termos-uso: served as static page (termos-uso/index.html)
  '/privacidade': 'https://exclusivo.contelege.com.br/politica-privacidade/',
  '/privacidade/': 'https://exclusivo.contelege.com.br/politica-privacidade/',
  '/politica-privacidade': 'https://exclusivo.contelege.com.br/politica-privacidade/',
  '/politica-privacidade/': 'https://exclusivo.contelege.com.br/politica-privacidade/',
  '/blog': 'https://blog.contelege.com.br/?utm_source=contelefleet&utm_medium=redirect',
  '/blog/': 'https://blog.contelege.com.br/?utm_source=contelefleet&utm_medium=redirect',
  '/contato': '/#planos',
  '/contato/': '/#planos',
  '/sobre': 'https://contele.io/?utm_source=contelefleet&utm_medium=redirect',
  '/sobre/': 'https://contele.io/?utm_source=contelefleet&utm_medium=redirect',
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
// Fleet: gatekeeping por quantidade de veiculos (nao de licencas/equipe).
// < MIN_VEHICLES -> NAO cria deal, grava planilha de leads pequenos,
// retorna { redirect: '/obrigado-2/' } pro frontend redirecionar.
const MIN_VEHICLES = 4;

const PIPEDRIVE_TOKEN = process.env.PIPEDRIVE_API_TOKEN;
const EVOLUTION_URL = process.env.EVOLUTION_API_URL || 'https://evolution-api-817d7afc.contele.io';
const EVOLUTION_KEY = process.env.EVOLUTION_API_KEY;
const EVOLUTION_INSTANCE = process.env.EVOLUTION_INSTANCE || 'Vendas n2';
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK_URL;
const DISCORD_WEBHOOK = process.env.DISCORD_WEBHOOK_URL_FLEET || process.env.DISCORD_WEBHOOK_URL || '';
// Canal dedicado pra falhas sensiveis (lead perdido, Pipe fail, sheet fail).
// Nao mistura com notificacoes normais pra nao afogar o sinal critico.
const DISCORD_LEAD_CRITICAL_WEBHOOK = process.env.DISCORD_LEAD_CRITICAL_WEBHOOK_URL || '';

// Planilha Fleet (growth#79). Mesma planilha do fluxo legado
// ([base leads GV Fleet] — 1LkTpcEbPqVfb...). Gravacao paridade 1:1 com
// producao: schema de keys bate com os headers reais da Página1 (a API
// ge-prd-web-api matcha por nome de header, nao posicional). `Processado='Sim'`
// neutraliza o Apps Script onChange (se algum estiver ativo), evitando
// duplicacao de deal.
//
// Depois da v1 estabilizar (Opcao B da task), trocamos pra Sheets API direta
// + aba dedicada. Por ora: mantem tudo na Página1 pra nao romper nada.
const SPREADSHEET_ID = process.env.SPREADSHEET_ID_FLEET || '1LkTpcEbPqVfb-zWviJHxme0saVGGt3anxg10oz1MjLc';
const SPREADSHEET_API_BASE = 'https://ge-prd-web-api.contele.com.br/api/v1/spreadsheet';

// URL fixa do webhook n8n Fleet SDR (mesmo workflow que o backend ge-prd-web-api chama hoje).
// Workflow: Y6D2XUPSRjaYKcJA (n8n-cloud, projeto Contele). Dispara Zapster msg1 + wait 15s + msg2 menu 1-9.
// Pode sobrescrever via env SDR_WEBHOOK_URL_FLEET em caso de rollover pra outro n8n.
const SDR_WEBHOOK = process.env.SDR_WEBHOOK_URL_FLEET
  || process.env.SDR_WEBHOOK_URL
  || 'https://marcofassa.app.n8n.cloud/webhook/sdr-fleet-n8n-v2';

// Formato de telefone identico ao Apps Script antigo: adiciona "55" se <=11 digitos.
function formatPhoneForN8n(rawPhone) {
  let cleaned = String(rawPhone || '').replace(/\D/g, '');
  if (cleaned.length <= 11) cleaned = '55' + cleaned;
  return cleaned;
}

// CEO Fleet: Julio Cesar. Flag NOTIFY_CEO liga/desliga o envio (Marco quer
// manter o que tem hoje, mas com escape hatch). Default: ligado.
const NOTIFY_CEO = (process.env.NOTIFY_CEO || 'true').toLowerCase() !== 'false';
const CEO_FLEET_PHONE = process.env.CEO_FLEET_PHONE || '5513997000902'; // Julio Cesar

// Contele OS (fonte de verdade de tracking GA4/UTM/gclid, issue growth#77)
const CONTELE_OS_URL = process.env.CONTELE_OS_URL || 'https://os.contele.io';
const CONTELE_OS_WEBHOOK_SECRET = process.env.CONTELE_OS_WEBHOOK_SECRET || '';
if (!CONTELE_OS_WEBHOOK_SECRET) {
  console.warn('[STARTUP] WARNING: CONTELE_OS_WEBHOOK_SECRET vazio! Tracking nao sera propagado pro Contele OS.');
}

// ===== Vendedores Fleet (round-robin 50/50) =====
// IDs Pipedrive confirmados via GET /users (api_token Contele).
// Round-robin alterna a cada deal criado com >= MIN_VEHICLES veiculos.
const ID_THIAGO = 4447438;
const ID_MARCIA = 13168743;
const VENDORS = {
  [ID_THIAGO]: { nome: 'Thiago Andrade', phone: '5511937083424' },
  [ID_MARCIA]: { nome: 'Marcia Gabriele', phone: '5513997143896' }
};
const VENDOR_IDS = [ID_THIAGO, ID_MARCIA]; // ordem de round-robin

// Pipedrive custom field keys (globais na conta, iguais pro Teams e Fleet)
const PD_FIELDS = {
  info: 'd32b1afb76380fd11b2979947d42701ca0ab1884',
  utm: 'f0fbb1341f09d81ca594898bab753004fb28b6ec',
  // "licencas" no Teams = "veiculos" no Fleet. Mesmo hash, reaproveitado.
  veiculos: '3c8d91b14db8b39066af6d9ccac83bba77382582',
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

async function sendWhatsApp(number, text) {
  if (!number) return;
  try {
    const r = await fetch(`${EVOLUTION_URL}/message/sendText/${encodeURIComponent(EVOLUTION_INSTANCE)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'apikey': EVOLUTION_KEY },
      body: JSON.stringify({ number, linkPreview: false, text })
    });
    if (!r.ok) {
      const body = await r.text().catch(() => '');
      console.error(`[WhatsApp] Evolution NON-OK [${r.status}] inst="${EVOLUTION_INSTANCE}" to=${number}: ${body.slice(0, 300)}`);
    } else {
      console.log(`[WhatsApp] sent inst="${EVOLUTION_INSTANCE}" to=${number}`);
    }
  } catch (err) {
    console.error(`[WhatsApp] send THROW inst="${EVOLUTION_INSTANCE}" to=${number}:`, err.message);
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
    await sendDiscord(`🚨 **Google Ads token refresh FAILED** (Fleet) | Conversions not uploading`);
    return err;
  }

  // Fleet customer ID: 3984015785 (398-401-5785)
  const customerId = (process.env.GOOGLE_ADS_CUSTOMER_ID_FLEET || process.env.GOOGLE_ADS_CUSTOMER_ID || '3984015785').replace(/-/g, '');
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
  const hour = parts.hour === '24' ? '00' : parts.hour;
  const tzRaw = parts.timeZoneName || 'GMT-03:00';
  const tzMatch = tzRaw.match(/GMT([+-]\d{1,2}(?::\d{2})?)/);
  let offset = '-03:00';
  if (tzMatch) {
    const raw = tzMatch[1];
    if (raw.includes(':')) {
      offset = raw.replace(/([+-])(\d)(:\d{2})/, '$1$20$3');
      if (offset.match(/^[+-]\d{1}$/)) offset = offset.replace(/([+-])(\d)$/, '$10$2:00');
    } else {
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

async function sendDiscordCritical(content) {
  // Fleet pode reusar o mesmo canal do Discord geral se o critical nao estiver
  // configurado. Preferencia: DISCORD_LEAD_CRITICAL_WEBHOOK_URL separado.
  const hook = DISCORD_LEAD_CRITICAL_WEBHOOK || DISCORD_WEBHOOK;
  if (!hook) return;
  try {
    await fetch(hook, {
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

// RD Station conversion via token publico. Duplica o que o hero dispara client-side
// (fleet-landing-hero-email-intent) com um evento completo quando o form principal e enviado.
// conversion_identifier semantico permite segmentar entre "intencao" (so digitou email no hero)
// e "lead completo" (preencheu formulario inteiro).
const RDSTATION_PUBLIC_TOKEN = 'aa36284ab8fe7a6454aa43ecd7a22704';
async function sendRdStationConversion(body, frota, ctaSource) {
  if (!body?.email) return;
  const payload = {
    event_type: 'CONVERSION',
    event_family: 'CDP',
    payload: {
      conversion_identifier: 'fleet-landing-form-completo',
      email: body.email,
      name: body.nome || '',
      mobile_phone: body.telefone || '',
      company_name: body.empresa || '',
      cf_veiculos: String(frota || ''),
      cf_cta: ctaSource || '',
      cf_campanha: body.campanha || body.utm_campaign || '',
      cf_gclid: body.gclid || '',
      cf_utm_source: body.utm_source || '',
      cf_utm_medium: body.utm_medium || '',
      cf_utm_term: body.utm_term || '',
      cf_utm_content: body.utm_content || '',
      traffic_source: (body.landing_page || '').slice(0, 500)
    }
  };
  try {
    const r = await fetch(`https://api.rd.services/platform/conversions?api_key=${RDSTATION_PUBLIC_TOKEN}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!r.ok) {
      const txt = await r.text().catch(() => '');
      console.error(`[RD] Conversion NON-OK [${r.status}] email=${body.email}:`, txt.slice(0, 200));
    } else {
      console.log(`[RD] Conversion OK email=${body.email} cta=${ctaSource}`);
    }
  } catch (err) {
    console.error(`[RD] Conversion THROW email=${body.email}:`, err.message);
  }
}

// Grava lead na planilha legada Fleet (Página1). Keys do `data` batem com os
// headers reais da aba — API ge-prd-web-api matcha por nome de header.
async function appendSheet(data) {
  const url = `${SPREADSHEET_API_BASE}/${SPREADSHEET_ID}`;
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ spreadsheetData: data })
    });
    if (!res.ok) {
      const body = await res.text().catch(() => '');
      console.error(`Sheets error [${res.status}]:`, body.slice(0, 300));
      sendDiscordCritical(
        `🚨 **appendSheet FAILED (Fleet)** [${res.status}]\n` +
        `Lead: ${data['Responsável'] || '?'} | ${data.Empresa || '?'} | ${data.WhatsApp || '?'}\n` +
        `Status: ${data.status || '?'} | Pipe ID: ${data['Pipe ID'] || 'sem'}\n` +
        `Body: ${body.slice(0, 200)}`
      ).catch(() => {});
      return false;
    }
    return true;
  } catch (err) {
    console.error('Sheets throw:', err.message);
    sendDiscordCritical(
      `🚨 **appendSheet THROW (Fleet)**\n` +
      `Lead: ${data['Responsável'] || '?'} | ${data.Empresa || '?'} | ${data.WhatsApp || '?'}\n` +
      `Status: ${data.status || '?'} | Pipe ID: ${data['Pipe ID'] || 'sem'}\n` +
      `Erro: ${err.message}`
    ).catch(() => {});
    return false;
  }
}

// Monta payload Página1 (19 colunas: E-mail, Empresa, Responsável, WhatsApp,
// Pessoa jurídica, Já utiliza rastreador?, Campanha, Representa órgão público?,
// Quantidade de Veiculos, Valor estimado por unidade, Valor total estimado,
// Referrer, Data de envio, WABA ID, Vendedor from Pipedrive, status, Info,
// Processado, Pipe ID). Processado='Sim' neutraliza Apps Script onChange.
function buildSheetDataFleet(body, frota, status, vendorName = '', dealId = '', infoText = '') {
  // Campanha: string UTM completa no formato legacy da Página1
  // (`utm_source=x&utm_medium=y&utm_campaign=z&...`). Se o frontend ja mandou
  // composta em body.campanha (algumas campanhas antigas), respeita; senao
  // monta via buildUtmString considerando body.campanha como campaign value.
  const composedUtm = buildUtmString(body);
  const campanha = (body.campanha && /[=&]/.test(body.campanha))
    ? body.campanha
    : composedUtm;
  return {
    'E-mail': body.email || '',
    'Empresa': body.empresa || '',
    'Responsável': body.nome || '',
    'WhatsApp': body.telefone || '',
    'Pessoa jurídica': 'Sim',
    'Já utiliza rastreador?': '',
    'Campanha': campanha,
    'Representa órgão público?': 'Não',
    'Quantidade de Veiculos': String(frota),
    'Valor estimado por unidade': 70,
    'Valor total estimado': 70 * frota,
    'Referrer': body.landing_page || body.page_url || body.source_url || '',
    'Data de envio': brDate(),
    'WABA ID': '',
    'Vendedor from Pipedrive': vendorName,
    'status': status,
    'Info': infoText,
    'Processado': 'Sim',
    'Pipe ID': dealId ? String(dealId) : ''
  };
}

// ===== Round-robin vendor assignment =====
// Persistido no Railway volume (sobrevive redeploys) pra nao resetar alternancia.
const fs = require('fs');
const DEDUP_DIR = process.env.RAILWAY_VOLUME_MOUNT_PATH || '/tmp';
const DEDUP_FILE = path.join(DEDUP_DIR, 'fired-conversions-fleet.json');
const VENDOR_STATE_FILE = path.join(DEDUP_DIR, 'vendor-round-robin-fleet.json');

function loadVendorState() {
  try {
    const data = JSON.parse(fs.readFileSync(VENDOR_STATE_FILE, 'utf8'));
    return { nextIndex: data.nextIndex || 0 };
  } catch {
    return { nextIndex: 0 };
  }
}

function saveVendorState(state) {
  try {
    fs.writeFileSync(VENDOR_STATE_FILE, JSON.stringify(state));
  } catch (err) {
    console.error('[VENDOR] Save state error:', err.message);
  }
}

const vendorState = loadVendorState();

function assignVendor() {
  // Alterna 50/50 entre Thiago e Marcia, persistindo state pra nao enviesar
  // em restarts. Simples: pega o proximo, avanca modulo.
  const id = VENDOR_IDS[vendorState.nextIndex % VENDOR_IDS.length];
  vendorState.nextIndex = (vendorState.nextIndex + 1) % VENDOR_IDS.length;
  saveVendorState(vendorState);
  return { id, ...VENDORS[id] };
}

function buildUtmString(body) {
  // Ordem espelha o formato legado Fleet na Pagina1 e na "Campanha" do Pipedrive:
  //   utm_campaign=X&utm_source=Y&utm_medium=Z&utm_term=W&utm_content=V
  // Mudar a ordem quebra dashboards de Mkt que fazem regex posicional.
  const parts = [];
  const campaign = body.utm_campaign || body.campanha;
  if (campaign) parts.push('utm_campaign=' + campaign);
  if (body.utm_source) parts.push('utm_source=' + body.utm_source);
  if (body.utm_medium) parts.push('utm_medium=' + body.utm_medium);
  if (body.utm_term) parts.push('utm_term=' + body.utm_term);
  if (body.utm_content) parts.push('utm_content=' + body.utm_content);
  return parts.join('&');
}

function brDate() {
  return new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });
}

// Remove query string e fragmento de uma URL. Mantem protocolo+host+path
// pra ficar <255 chars em quase todo caso (proteje Pipedrive varchar).
function stripQuery(url) {
  if (!url) return '';
  try {
    const u = new URL(url);
    return u.origin + u.pathname;
  } catch {
    // fallback: remove manualmente se URL for malformada
    const idx = url.search(/[?#]/);
    return idx === -1 ? url : url.slice(0, idx);
  }
}

// ===== LEAD ENDPOINT =====
// Fleet usa `tamanho_frota` (numero de veiculos) no lugar de `tamanho_equipe`.
// Aceita ambos no body pro caso do form mandar o nome antigo.
app.post('/api/lead', async (req, res) => {
  const body = req.body;
  const frota = parseInt(body.tamanho_frota || body.tamanho_equipe, 10) || 0;

  const ctaSource = body.cta_source || 'consultor';
  console.log(`[LEAD-FLEET] ${body.nome} | ${body.empresa} | ${frota} veiculos | cta=${ctaSource} | gclid=${body.gclid ? 'yes' : 'no'}`);

  // ===== GATEKEEPING: < MIN_VEHICLES =====
  // Fleet NAO cria deal pra quem tem menos de 4 veiculos. Grava planilha e
  // RETORNA flag pro frontend redirecionar pra /obrigado-2/ (pagina de "ops,
  // nao e pra voce"). Diferente do Teams que sempre respondia { ok: true }.
  const isTest = /teste|test|prova|fake/i.test(body.nome || '') ||
                 /teste|test|fake|@contele\.com/i.test(body.email || '') ||
                 /contele/i.test(body.empresa || '');

  if (!isTest && frota < MIN_VEHICLES) {
    // Resposta sincrona com flag de redirect, depois grava sheet em background
    res.json({ ok: true, redirect: '/obrigado-2/', reason: 'below_min_vehicles' });

    const sheetData = buildSheetDataFleet(
      body, frota, '4_lead_inadequado', '', '', `CTA: ${ctaSource} (inadequado)`
    );
    appendSheet(sheetData).catch(err => console.error('[LEAD-FLEET] Sheet inadequado error:', err.message));
    console.log(`[LEAD-FLEET] Inadequado: ${body.nome} (${frota} veic) -> sheet only, redirect /obrigado-2/`);
    return;
  }

  // Quick response to frontend (lead valido, processa em background)
  res.json({ ok: true, redirect: '/obrigado/' });

  try {
    await processLead(body, frota, ctaSource, isTest);
  } catch (err) {
    console.error('[LEAD-FLEET] Handler crashed:', err);
    await sendDiscordCritical(
      `🚨 **LEAD FLEET HANDLER CRASHED** (possivel lead perdido)\n` +
      `Lead: ${body?.nome || '?'} | ${body?.empresa || '?'} | ${body?.telefone || '?'} | ${body?.email || '?'}\n` +
      `Veiculos: ${frota} | CTA: ${ctaSource}\n` +
      `Erro: ${err.message}\n\`\`\`${(err.stack || '').slice(0, 400)}\`\`\``
    ).catch(() => {});
  }
});

async function processLead(body, frota, ctaSource, isTest) {
  const ctaLabel = { consultor: 'Fale com Consultor', testar: 'Teste Grátis', especialista: 'Falar com Especialista', contratar: 'Contratar Agora' }[ctaSource] || ctaSource;
  const infoText = `CTA: ${ctaLabel}. ${body.info || ''}`.trim();

  // Filter test submissions: log to sheet but skip Pipedrive/SDR/notifications
  if (isTest) {
    const sheetData = buildSheetDataFleet(body, frota, '3-temp-can-delete-teste', '', '', infoText);
    await appendSheet(sheetData);
    console.log(`[LEAD-FLEET] TEST FILTERED: ${body.nome} -> sheet only`);
    return;
  }

  // ===== LEAD QUALIFICADO (>= MIN_VEHICLES) =====
  const vendor = assignVendor();
  const utmString = buildUtmString(body);

  // 1. Create Person in Pipedrive
  const personRes = await pipedrivePost('persons', {
    name: body.nome,
    email: [body.email],
    phone: [body.telefone]
  });
  const personId = personRes.ok ? personRes.data?.data?.id : null;

  if (!personRes.ok || !personId) {
    const sheetData = buildSheetDataFleet(body, frota, '5_pipedrive_person_failed', '', '', infoText);
    await appendSheet(sheetData);
    await sendDiscordCritical(
      `🚨 **Pipedrive PERSON FAILED (Fleet)** (lead nao virou deal)\n` +
      `Lead: ${body.nome} | ${body.empresa} | ${body.telefone} | ${body.email}\n` +
      `Veiculos: ${frota} | CTA: ${ctaSource}\n` +
      `Status: ${personRes.status} | Erro: ${JSON.stringify(personRes.error).slice(0, 200)}`
    ).catch(() => {});
    console.error(`[LEAD-FLEET] ABORT: person creation failed for ${body.empresa}`);
    return;
  }

  // 2. Create Deal in Pipedrive (Pipeline 1 Fleet, stage 2 CONTATANDO)
  const dealBody = {
    title: body.empresa || body.nome,
    person_id: personId,
    stage_id: 2,       // 2 CONTATANDO (Fleet)
    pipeline_id: 1,    // Pipeline 1 (Fleet)
    user_id: vendor.id,
    value: frota,
    currency: 'BRL',
    visible_to: 3,
    status: 'open'
  };
  dealBody[PD_FIELDS.info] = infoText;
  dealBody[PD_FIELDS.utm] = utmString;
  dealBody[PD_FIELDS.veiculos] = frota;
  // Pipedrive custom fields sao varchar(255) por padrao. landing_page completo
  // (com gclid + UTMs) facilmente ultrapassa isso e trunca GCLID no meio.
  // GCLID e UTMs ja vao em campos dedicados (51bccf... e f0fbb1...) full size,
  // entao "Origem" grava apenas protocolo+host+path sem query string.
  dealBody[PD_FIELDS.origem] = stripQuery(body.landing_page);
  dealBody[PD_FIELDS.gclid] = body.gclid || '';
  dealBody[PD_FIELDS.ga4] = body.ga4_client_id || '';

  // Safety: Pipedrive custom fields sao varchar(255). GCLID real do Google Ads
  // tem ~90-110 chars (bem abaixo do limite), mas edge cases podem truncar.
  // Fallback: URL full com gclid fica na coluna "Referrer" da planilha e no
  // campo raw_gclid do webhook Contele OS. Warn pra audit.
  if (body.gclid && body.gclid.length > 200) {
    console.warn(`[GCLID-WARN] deal=${dealBody.title} gclid.length=${body.gclid.length} (limite Pipe 255). Full fica em Sheets/Contele OS.`);
  }

  const dealRes = await pipedrivePost('deals', dealBody);
  const dealId = dealRes.ok ? dealRes.data?.data?.id : null;

  if (!dealRes.ok || !dealId) {
    const sheetData = buildSheetDataFleet(body, frota, '5_pipedrive_deal_failed', vendor.nome, '', infoText);
    await appendSheet(sheetData);
    await sendDiscordCritical(
      `🚨 **Pipedrive DEAL FAILED (Fleet)** (person criada mas deal nao, lead orfao)\n` +
      `Lead: ${body.nome} | ${body.empresa} | ${body.telefone} | ${body.email}\n` +
      `Veiculos: ${frota} | CTA: ${ctaSource}\n` +
      `Person ID: ${personId}\n` +
      `Status: ${dealRes.status} | Erro: ${JSON.stringify(dealRes.error).slice(0, 200)}`
    ).catch(() => {});
    console.error(`[LEAD-FLEET] ABORT: deal creation failed for ${body.empresa} (person=${personId})`);
    return;
  }

  console.log(`[LEAD-FLEET] Pipedrive: person=${personId} deal=${dealId} vendor=${vendor.nome}`);

  // 2b. Propaga tracking completo pro Contele OS (fire-and-forget)
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

  // 3. Build sheet payload com schema legacy Página1 (Processado='Sim' evita
  // Apps Script onChange duplicar deal).
  const sheetData = buildSheetDataFleet(
    body, frota, '1-success-deal-created-in-pipedrive', vendor.nome, dealId, infoText
  );

  // 4. Run remaining tasks in parallel
  const pipedriveUrl = `https://contelegv.pipedrive.com/deal/${dealId}`;
  const waLink = `https://wa.me/${body.telefone}`;
  const faixa = frota >= 50 ? 'Grande (50+)' : frota >= 10 ? 'Media (10-49)' : 'Pequena (4-9)';

  const notifText = [
    `Novo lead Fleet!`,
    ``,
    `${body.empresa} | ${frota} veiculos | ${faixa}`,
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
    `:rocket: *Novo lead Fleet!*`,
    ``,
    `>*${body.empresa}* | ${frota} veiculos | ${faixa}`,
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

  const tasks = [
    appendSheet(sheetData),
    sendSlack(slackText),
    sendWhatsApp(VENDORS[vendor.id]?.phone, notifText),
    sendRdStationConversion(body, frota, ctaSource)
  ];

  // CEO notify (flag NOTIFY_CEO). Default: ligado (manter o que tem hoje).
  if (NOTIFY_CEO && CEO_FLEET_PHONE) {
    tasks.push(sendWhatsApp(CEO_FLEET_PHONE, notifText));
  }

  // SDR webhook n8n Fleet — payload bate 1:1 com producao (ge-prd-web-api -> n8n).
  // Schema confirmado via execucao real 21/04/2026 do workflow Y6D2XUPSRjaYKcJA:
  //   nome, whatsapp, email, pipedrive_id, vehicle_count, company,
  //   idUsuarioPipedrive, info, vendedor, Campanha, Referrer
  // Trocar nomes quebra o Zapster node (espera body.whatsapp como recipient) e
  // o JS code "define vendedor" (espera body.vendedor e body.nome).
  if (SDR_WEBHOOK) {
    const campaignStr = body.campanha || [
      body.utm_campaign ? `utm_campaign=${body.utm_campaign}` : '',
      body.utm_source ? `utm_source=${body.utm_source}` : '',
      body.utm_medium ? `utm_medium=${body.utm_medium}` : '',
      body.utm_term ? `utm_term=${body.utm_term}` : '',
      body.utm_content ? `utm_content=${body.utm_content}` : ''
    ].filter(Boolean).join('&');

    const n8nPayload = {
      nome: body.nome || '',
      whatsapp: formatPhoneForN8n(body.telefone),
      email: body.email || '',
      pipedrive_id: dealId || 0,
      vehicle_count: frota,
      company: body.empresa || '',
      idUsuarioPipedrive: vendor.id,
      info: body.info || '',
      vendedor: vendor.nome,
      Campanha: campaignStr,
      Referrer: body.landing_page || body.page_url || body.source_url || ''
    };

    tasks.push(
      fetch(SDR_WEBHOOK, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(n8nPayload)
      }).then(async (sdrRes) => {
        if (!sdrRes.ok) {
          const txt = await sdrRes.text().catch(() => '');
          console.error(`SDR webhook non-OK [${sdrRes.status}]:`, txt.slice(0, 200));
          sendDiscordCritical(
            `🚨 **SDR webhook NON-OK (Fleet)** [${sdrRes.status}]\n` +
            `Lead: ${body.nome} | ${body.empresa} | ${body.telefone}\n` +
            `Deal: ${dealId} | Veiculos: ${frota}\n` +
            `Body: ${txt.slice(0, 200)}`
          ).catch(() => {});
        }
      }).catch(err => {
        console.error('SDR webhook error:', err.message);
        sendDiscordCritical(
          `🚨 **SDR webhook THROW (Fleet)**\n` +
          `Lead: ${body.nome} | ${body.empresa} | ${body.telefone}\n` +
          `Deal: ${dealId} | Veiculos: ${frota}\n` +
          `Erro: ${err.message}`
        ).catch(() => {});
      })
    );
  }

  await Promise.allSettled(tasks);

  // Discord notify (Momento 1: lead novo entrou). Fire-and-forget, nao bloqueia response.
  sendDiscord(
    `🆕 **Novo lead Fleet**\n\n` +
    `**${body.empresa}** • ${frota} veiculos\n` +
    `Lead: ${body.nome}\n` +
    `Contato: ${body.email} | ${body.telefone}\n` +
    `Fonte: ${body.gclid ? 'Google Ads (GCLID ✓)' : 'orgânico'} | UTM: ${body.utm_source || '-'}/${body.utm_medium || '-'}\n` +
    `CTA: ${ctaSource} | Vendor: ${vendor.nome}\n` +
    `Pipedrive: <https://contelegv.pipedrive.com/deal/${dealId}>`
  ).catch(() => {});

  console.log(`[LEAD-FLEET] Complete: ${body.empresa} -> deal ${dealId}, vendor ${vendor.nome}`);
}

// ===== PIPEDRIVE WEBHOOK: Deal Stage Change =====
const GOOGLE_ADS_CONVERSION_URL = 'https://www.google-analytics.com/mp/collect';
const GA4_MEASUREMENT_ID = process.env.GA4_MEASUREMENT_ID_FLEET || process.env.GA4_MEASUREMENT_ID || 'G-EQD5JNT9PS';
const GA4_API_SECRET = process.env.GA4_API_SECRET_FLEET || process.env.GA4_API_SECRET || '';

// Pipeline 1 (Fleet) stages que contam como "qualified"
const QUALIFIED_STAGES = [157, 263, 3, 155];

// Pipeline 1 (Fleet) stages won
const WON_STAGES = [259, 270, 281, 282, 283, 240];

// Pipeline 1 (Fleet) stage LOST
const LOST_STAGE = 241;

// Conversion Actions Fleet (customer 3984015785)
const GADS_CONV_QUALIFIED = process.env.GADS_CONV_QUALIFIED_FLEET || 'customers/3984015785/conversionActions/7446455655';
const GADS_CONV_WON = process.env.GADS_CONV_WON_FLEET || 'customers/3984015785/conversionActions/7453621406';

// Dedup: persist fired conversions to Railway volume
const DEDUP_FILE_FLEET = DEDUP_FILE;

function loadDedup() {
  try {
    const data = JSON.parse(fs.readFileSync(DEDUP_FILE_FLEET, 'utf8'));
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
    fs.writeFileSync(DEDUP_FILE_FLEET, JSON.stringify({
      qualified: [...firedQualified],
      won: [...firedWon]
    }));
  } catch (err) {
    console.error('[DEDUP] Save error:', err.message);
  }
}

const { qualified: firedQualified, won: firedWon } = loadDedup();
console.log(`[DEDUP] Fleet loaded: ${firedQualified.size} qualified, ${firedWon.size} won`);

// Startup health checks
if (!GA4_API_SECRET) console.warn('[STARTUP] WARNING: GA4_API_SECRET_FLEET is empty! GA4 Measurement Protocol events will NOT be sent.');
if (!SLACK_WEBHOOK) console.warn('[STARTUP] WARNING: SLACK_WEBHOOK_URL is empty! Slack notifications disabled.');
if (!DISCORD_WEBHOOK) console.warn('[STARTUP] WARNING: DISCORD_WEBHOOK_URL_FLEET is empty! Discord notifications disabled.');
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
        console.warn('[PIPE-DELETE-FLEET] no deal_id em delete event:', JSON.stringify(req.body).slice(0, 400));
        return;
      }

      // Pipeline 1 = Fleet. Outros pipelines: ignorar.
      if (pipelineId && pipelineId !== 1) {
        console.log(`[PIPE-DELETE-FLEET] ignorando deal=${dealId} pipeline=${pipelineId} (nao-Fleet)`);
        return;
      }

      console.log(`[PIPE-DELETE-FLEET] forward deal=${dealId} pipeline=${pipelineId || 'n/a'} -> contele-os`);

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
          .then(r => console.log(`[PIPE-DELETE-FLEET] OS resp ${r.status} deal=${dealId}`))
          .catch(err => console.error(`[PIPE-DELETE-FLEET] OS dispatch fail deal=${dealId}:`, err.message));
      } else {
        console.warn(`[PIPE-DELETE-FLEET] CONTELE_OS_WEBHOOK_SECRET vazio, skip dispatch deal=${dealId}`);
      }

      const hook = DISCORD_LEAD_CRITICAL_WEBHOOK || DISCORD_WEBHOOK;
      if (hook) {
        fetch(hook, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content: `🗑️ Pipedrive delete (Fleet): deal=${dealId} -> contele-os/sales-lead-delete`
          })
        }).catch(() => {});
      }

      return;
    }

    const current = req.body.data || req.body.current || {};
    const previous = req.body.previous || {};
    if (!current.id) return;

    const dealId = current.id;
    const newStageId = parseInt(current.stage_id, 10);
    const oldStageId = parseInt(previous?.stage_id, 10) || 0;
    const pipelineId = parseInt(current.pipeline_id, 10);
    const status = current.status;

    console.log(`[PIPE-FLEET] Received: deal=${dealId} pipeline=${pipelineId} stage=${oldStageId}->${newStageId} status=${status}`);

    // Only process Pipeline 1 (Fleet)
    if (pipelineId !== 1) return;

    const prevStatus = previous?.status;
    const prevStageExists = previous?.stage_id !== undefined && previous?.stage_id !== null;
    const stageChanged = prevStageExists && oldStageId !== newStageId;
    const statusChangedToWon = status === 'won' && prevStatus !== undefined && prevStatus !== 'won';

    if (!stageChanged && !statusChangedToWon) {
      console.log(`[PIPE-FLEET] Ignoring: deal=${dealId} no stage change (prev_stage=${prevStageExists ? oldStageId : 'N/A'}->${newStageId}) no won change (prev_status=${prevStatus || 'N/A'})`);
      return;
    }

    function getCustomField(fieldKey) {
      const cf = current.custom_fields?.[fieldKey];
      if (cf && typeof cf === 'object') return cf.value || '';
      if (cf) return cf;
      return current[fieldKey] || '';
    }

    const gclidFromPipe = getCustomField(PD_FIELDS.gclid);
    const ga4ClientIdFromPipe = getCustomField(PD_FIELDS.ga4);
    const utmRaw = getCustomField(PD_FIELDS.utm);
    const dealValue = current.value || 0;
    const dealTitle = current.title || '';

    const utmParamsFromPipe = Object.fromEntries(new URLSearchParams(utmRaw));

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
            console.log(`[PIPE-FLEET] Tracking do Contele OS: deal=${dealId} sid=${ga4SessionId ? 'yes' : 'no'} cid=${ga4ClientId ? 'yes' : 'no'} ec=${hashedEmail ? 'yes' : 'no'}`);
          } else {
            console.log(`[PIPE-FLEET] Contele OS lookup: deal=${dealId} not_found, fallback Pipedrive`);
          }
        } else {
          console.warn(`[PIPE-FLEET] Contele OS lookup NON-OK [${lookup.status}] deal=${dealId}, fallback Pipedrive`);
        }
      } catch (err) {
        console.error(`[PIPE-FLEET] Contele OS lookup THROW deal=${dealId}:`, err.message);
      }
    }

    console.log(`[PIPE-FLEET] Deal ${dealId} "${dealTitle}" | gclid=${gclid ? 'yes' : 'no'} | ga4_cid=${ga4ClientId ? 'yes' : 'no'} | ga4_sid=${ga4SessionId ? 'yes' : 'no'}`);

    // QUALIFIED: deal entered a qualified stage (fire only once per deal)
    if (QUALIFIED_STAGES.includes(newStageId) && !QUALIFIED_STAGES.includes(oldStageId) && !firedQualified.has(dealId)) {
      firedQualified.add(dealId); saveDedup();
      console.log(`[PIPE-FLEET] QUALIFIED: ${dealTitle} (deal ${dealId}) | GCLID: ${gclid}`);

      let ga4Status = 'skipped';
      if (!GA4_API_SECRET) {
        console.warn(`[PIPE-FLEET] GA4_API_SECRET is empty! GA4 events NOT being sent for deal ${dealId}`);
        ga4Status = 'FAILED (no API secret)';
      } else if (ga4ClientId) {
        try {
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
            console.log(`[PIPE-FLEET] GA4 lead_qualificado sent for deal ${dealId} (HTTP ${ga4Resp.status})`);
          } else {
            ga4Status = `FAILED (HTTP ${ga4Resp.status})`;
            console.error(`[PIPE-FLEET] GA4 lead_qualificado FAILED for deal ${dealId}: HTTP ${ga4Resp.status}`);
          }
        } catch (err) {
          ga4Status = `FAILED (${err.message})`;
          console.error('[PIPE-FLEET] GA4 error:', err.message);
        }
      } else {
        ga4Status = 'skipped (no client ID)';
      }

      let gadsStatus = 'skipped (no full GCLID)';
      if (gclid && gclid.length >= 80) {
        try {
          const adsResult = await uploadGoogleAdsConversion(
            gclid,
            GADS_CONV_QUALIFIED,
            1.0,
            brConversionDateTime(),
            hashedEmail,
            hashedPhone
          );
          if (adsResult.success) {
            gadsStatus = 'SUCCESS';
            console.log(`[PIPE-FLEET] Google Ads upload SUCCESS (qualified) deal=${dealId}`);
          } else {
            gadsStatus = `FAILED: ${adsResult.failureReason || 'unknown'}`;
            console.error(`[PIPE-FLEET] Google Ads upload FAILED (qualified) deal=${dealId}: ${adsResult.failureReason}`);
            await sendDiscord(`🚨 **Google Ads upload FAILED (Fleet)** (lead_qualificado) deal=${dealId}\nReason: ${adsResult.failureReason}\nGCLID: ${gclid.slice(0, 30)}...`);
          }
        } catch (err) {
          gadsStatus = `ERROR: ${err.message}`;
          console.error(`[PIPE-FLEET] Google Ads upload error (qualified) deal=${dealId}:`, err.message);
          await sendDiscord(`🚨 **Google Ads upload ERROR (Fleet)** (lead_qualificado) deal=${dealId}: ${err.message}`);
        }
      }

      await sendSlack(`:star: *Lead Fleet qualificado!*\n\n*${dealTitle}* entrou em etapa avançada\nGCLID: ${gclid ? 'sim' : 'nao'}\nGoogle Ads: ${gadsStatus}\nGA4: ${ga4Status}\n<https://contelegv.pipedrive.com/deal/${dealId}|Abrir no Pipedrive>`);
      await sendDiscord(`⭐ **Lead Fleet qualificado!**\n\n**${dealTitle}** entrou em etapa avançada\nGCLID: ${gclid || 'N/A'}\nGA4 Client ID: ${ga4ClientId || 'N/A'}\nGA4: ${ga4Status}\nGoogle Ads: ${gadsStatus}\nPipedrive: <https://contelegv.pipedrive.com/deal/${dealId}>`);
    }

    // WON: deal closed as won (fire only once per deal)
    if ((statusChangedToWon || (WON_STAGES.includes(newStageId) && !WON_STAGES.includes(oldStageId))) && !firedWon.has(dealId)) {
      firedWon.add(dealId); saveDedup();
      console.log(`[PIPE-FLEET] WON: ${dealTitle} (deal ${dealId}) | value: ${dealValue} | GCLID: ${gclid}`);

      let ga4WonStatus = 'skipped';
      if (!GA4_API_SECRET) {
        console.warn(`[PIPE-FLEET] GA4_API_SECRET is empty! GA4 events NOT being sent for deal ${dealId}`);
        ga4WonStatus = 'FAILED (no API secret)';
      } else if (ga4ClientId) {
        try {
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
            console.log(`[PIPE-FLEET] GA4 lead_convertido sent for deal ${dealId}, value ${dealValue} (HTTP ${ga4Resp.status})`);
          } else {
            ga4WonStatus = `FAILED (HTTP ${ga4Resp.status})`;
            console.error(`[PIPE-FLEET] GA4 lead_convertido FAILED for deal ${dealId}: HTTP ${ga4Resp.status}`);
          }
        } catch (err) {
          ga4WonStatus = `FAILED (${err.message})`;
          console.error('[PIPE-FLEET] GA4 error:', err.message);
        }
      } else {
        ga4WonStatus = 'skipped (no client ID)';
      }

      let gadsWonStatus = 'skipped (no full GCLID)';
      if (gclid && gclid.length >= 80) {
        try {
          const adsResult = await uploadGoogleAdsConversion(
            gclid,
            GADS_CONV_WON,
            dealValue || 1.0,
            brConversionDateTime(),
            hashedEmail,
            hashedPhone
          );
          if (adsResult.success) {
            gadsWonStatus = 'SUCCESS';
            console.log(`[PIPE-FLEET] Google Ads upload SUCCESS (won) deal=${dealId}, value ${dealValue}`);
          } else {
            gadsWonStatus = `FAILED: ${adsResult.failureReason || 'unknown'}`;
            console.error(`[PIPE-FLEET] Google Ads upload FAILED (won) deal=${dealId}: ${adsResult.failureReason}`);
            await sendDiscord(`🚨 **Google Ads upload FAILED (Fleet)** (lead_convertido) deal=${dealId} value=${dealValue}\nReason: ${adsResult.failureReason}\nGCLID: ${gclid.slice(0, 30)}...`);
          }
        } catch (err) {
          gadsWonStatus = `ERROR: ${err.message}`;
          console.error(`[PIPE-FLEET] Google Ads upload error (won) deal=${dealId}:`, err.message);
          await sendDiscord(`🚨 **Google Ads upload ERROR (Fleet)** (lead_convertido) deal=${dealId}: ${err.message}`);
        }
      }

      await sendSlack(`:tada: *Deal Fleet ganho!*\n\n*${dealTitle}* virou cliente\nValor: ${dealValue} veiculos\nGCLID: ${gclid ? 'sim' : 'nao'}\nGoogle Ads: ${gadsWonStatus}\nGA4: ${ga4WonStatus}\n<https://contelegv.pipedrive.com/deal/${dealId}|Abrir no Pipedrive>`);
      await sendDiscord(`🎉 **Deal Fleet ganho!**\n\n**${dealTitle}** virou cliente\nValor: ${dealValue} veiculos\nGCLID: ${gclid || 'N/A'}\nGA4 Client ID: ${ga4ClientId || 'N/A'}\nGA4: ${ga4WonStatus}\nGoogle Ads: ${gadsWonStatus}\nPipedrive: <https://contelegv.pipedrive.com/deal/${dealId}>`);
    }

    // LOST: apenas loga, nao dispara conversao (info pra debug/alerta futuro)
    if (newStageId === LOST_STAGE && oldStageId !== LOST_STAGE) {
      console.log(`[PIPE-FLEET] LOST: ${dealTitle} (deal ${dealId}) moveu pra stage ${LOST_STAGE}`);
    }

  } catch (err) {
    console.error('[PIPE-FLEET] FATAL ERROR:', err.message, err.stack);
    await sendDiscord(`🚨 **ERRO no webhook Pipedrive Fleet!**\n\n\`\`\`${err.message}\n${err.stack?.slice(0, 300)}\`\`\`\n\nPayload keys: ${Object.keys(req.body || {}).join(', ')}\nDeal ID: ${req.body?.data?.id || req.body?.current?.id || '?'}`).catch(() => {});
    await sendSlack(`:rotating_light: *ERRO webhook Pipedrive Fleet:* ${err.message}\nDeal: ${req.body?.data?.id || '?'}`).catch(() => {});
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
app.listen(PORT, () => console.log(`ConTele Fleet landing running on :${PORT}`));
