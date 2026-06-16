require('dotenv').config({ path: '.env.local' });
const express = require('express');
const HTMLtoDOCX = require('html-to-docx');

const app = express();
app.use(express.json({ limit: '10mb' }));
app.use(express.static(__dirname));

const N8N_WEBHOOK = 'https://primary-production-2349.up.railway.app/webhook/politica-frota-upload';

// ── Converte HTML → DOCX → envia para n8n → retorna link do Google Doc ──
app.post('/api/gdoc/create', async (req, res) => {
  const { html, empresa, nomePolitica } = req.body;
  if (!html) return res.status(400).json({ error: 'html obrigatório' });

  try {
    const docxBuffer = await HTMLtoDOCX(html, null, { footer: false, pageNumber: false });
    const buf = Buffer.isBuffer(docxBuffer) ? docxBuffer : Buffer.from(docxBuffer);
    const docxBase64 = buf.toString('base64');

    const n8nRes = await fetch(N8N_WEBHOOK, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ docxBase64, empresa: empresa || 'Empresa', nomePolitica: nomePolitica || 'Política de Frota' }),
    });

    const data = await n8nRes.json();
    if (!data.docUrl) throw new Error('n8n não retornou docUrl');
    res.json({ docUrl: data.docUrl });
  } catch (err) {
    console.error('Erro ao criar Google Doc:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── Captura de lead no RD Station ──
app.post('/api/lead', async (req, res) => {
  const { email, responsavel, empresa, whatsapp } = req.body;
  try {
    const response = await fetch(
      `https://api.rd.services/platform/conversions?api_key=${process.env.RD_API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', accept: 'application/json' },
        body: JSON.stringify({
          event_type: 'CONVERSION',
          event_family: 'CDP',
          payload: {
            conversion_identifier: 'gv-gerador-politica-de-frota',
            email,
            name: responsavel,
            company_name: empresa,
            mobile_phone: whatsapp
          }
        })
      }
    );
    const data = await response.json();
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

const PORT = process.env.PORT || 3030;
app.listen(PORT, () => console.log(`Servidor rodando em http://localhost:${PORT}`));
