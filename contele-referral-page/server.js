const express = require('express');
const path = require('path');
const app = express();

// Trust proxy - equivalente ao ProxyFix do Python/Flask
// Necessário para funcionar atrás de Cloudflare + Railway
app.set('trust proxy', 1);

// Serve static files from dist/
app.use(express.static(path.join(__dirname, 'dist')));

// SPA fallback - todas as rotas vão para index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on port ${PORT}`);
});
