require('dotenv').config({ path: '.env.local' });
const express = require('express');
const app = express();

app.use(express.json());
app.use(express.static(__dirname));

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
