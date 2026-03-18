const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.static(path.join(__dirname, 'public')));

app.get('/privacy', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'privacy.html'));
});

app.get('/privacidade', (req, res) => {
  res.redirect(301, '/privacy');
});

app.listen(PORT, () => {
  console.log(`contele.io running on port ${PORT}`);
});
