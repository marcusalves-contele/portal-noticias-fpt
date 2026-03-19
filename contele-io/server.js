const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));

// Página principal: detecta domínio pra servir pt-BR ou en
app.get('/', (req, res) => {
  const host = req.hostname || '';
  if (host.includes('contele.io')) {
    res.sendFile(path.join(__dirname, 'public', 'index-en.html'));
  } else {
    // contele.com.br ou qualquer outro
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
  }
});

// Preview da nova página (manter temporariamente)
app.get('/nova', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Versão inglês acessível diretamente
app.get('/en', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index-en.html'));
});

// Privacidade
app.get('/privacy', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'privacy.html'));
});

app.get('/privacidade', (req, res) => {
  res.redirect(301, '/privacy');
});

// Redirects legados
app.get('/whatsapp', (req, res) => {
  res.redirect(301, 'https://api.whatsapp.com/send/?phone=5511971325108');
});

app.get('/atendimento', (req, res) => {
  res.redirect(301, 'https://api.whatsapp.com/send/?phone=5511971325108');
});

app.listen(PORT, () => {
  console.log(`contele.io running on port ${PORT}`);
});
