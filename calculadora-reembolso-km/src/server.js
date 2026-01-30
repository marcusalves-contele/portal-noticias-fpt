/**
 * Express Server - Calculadora Reembolso KM
 * Backend API para salvar resultados e usuarios
 */

const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const apiRoutes = require('./routes/api');

const app = express();
const PORT = process.env.PORT || 3000;

// CORS configuration - restrict to specific origins
const allowedOrigins = [
  'https://calculadora-reembolso-km-production.up.railway.app',
  'https://calculadora.conteleteams.com.br',
  'https://conteleteams.com.br',
  'http://localhost:3000'
];

app.use(cors({
  origin: function(origin, callback) {
    // Allow requests with no origin (like mobile apps, curl, same-origin)
    if (!origin) return callback(null, true);

    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      // In production, reject unknown origins. In dev, allow all for testing.
      if (process.env.NODE_ENV === 'production') {
        callback(new Error('CORS not allowed'), false);
      } else {
        callback(null, true);
      }
    }
  },
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type']
}));

// Body parser
app.use(express.json());

// JSON parse error handler
app.use((err, req, res, next) => {
  if (err instanceof SyntaxError && err.status === 400 && 'body' in err) {
    return res.status(400).json({ error: 'JSON invalido' });
  }
  next(err);
});

app.use(express.urlencoded({ extended: true }));

// Static files
app.use(express.static(path.join(__dirname, '../public')));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// API routes
app.use('/api', apiRoutes);

// 404 handler for API routes
app.use('/api', (req, res) => {
  res.status(404).json({ error: 'Rota nao encontrada' });
});

// SPA fallback - serve index.html for non-API routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

// Error handler
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Erro interno do servidor' });
});

// Start server only if not in test mode
if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
  });
}

module.exports = app;
