const express = require('express');
const path = require('path');

const app = express();
app.use(express.json());

// ===== HEALTH CHECK (before static) =====
app.get('/health', (req, res) => res.json({ ok: true, ts: new Date().toISOString() }));

// Static files
app.use(express.static(path.join(__dirname), { extensions: ['html'] }));

// ===== CONFIG =====
const MIN_TEAM_SIZE = 4;

const PIPEDRIVE_TOKEN = process.env.PIPEDRIVE_API_TOKEN;
const EVOLUTION_URL = process.env.EVOLUTION_API_URL || 'https://evolution-api-817d7afc.contele.io';
const EVOLUTION_KEY = process.env.EVOLUTION_API_KEY;
const EVOLUTION_INSTANCE = process.env.EVOLUTION_INSTANCE || 'Vendas n2';
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK_URL;
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
  const notifText = [
    `Novo lead!`,
    ``,
    `Empresa: ${body.empresa}`,
    `Usuarios: ${tamanho}`,
    ``,
    `Responsavel: ${body.nome}`,
    `Telefone: ${body.telefone}`,
    `Email: ${body.email}`,
    `Campanha: ${body.campanha || 'N/A'}`,
    `Vendedor: ${vendor.nome}`,
    `Pipedrive: ${pipedriveUrl}`
  ].join('\n');

  const slackText = [
    `:rocket: *Novo lead!*`,
    ``,
    `*Empresa:* ${body.empresa}`,
    `*Usuarios:* ${tamanho}`,
    ``,
    `• *Email:* ${body.email}`,
    `• *Responsavel:* ${body.nome}`,
    `• *Telefone:* ${body.telefone}`,
    `• *Campanha:* ${body.campanha || 'N/A'}`,
    `• *GCLID:* ${body.gclid || 'N/A'}`,
    `• *Vendedor:* ${vendor.nome}`,
    `• *Pipedrive:* ${pipedriveUrl}`
  ].join('\n');

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
    }).catch(err => console.error('SDR webhook error:', err.message))
  ]);

  console.log(`[LEAD] Complete: ${body.empresa} -> deal ${dealId}, vendor ${vendor.nome}`);
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
