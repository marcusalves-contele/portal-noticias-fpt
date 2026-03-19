const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));

app.get('/nova', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/privacy', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'privacy.html'));
});

app.get('/privacidade', (req, res) => {
  res.redirect(301, '/privacy');
});

// Redirects legados (existiam no S3/servidor antigo)
app.get('/whatsapp', (req, res) => {
  res.redirect(301, 'https://api.whatsapp.com/send/?phone=5511971325108');
});

app.get('/atendimento', (req, res) => {
  res.redirect(301, 'https://api.whatsapp.com/send/?phone=5511971325108');
});

app.listen(PORT, () => {
  console.log(`contele.io running on port ${PORT}`);
});
