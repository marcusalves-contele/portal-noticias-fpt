const express = require('express');
const compression = require('compression');

const app = express();
app.use(compression());
app.use(express.json());

app.get('/health', (req, res) => res.json({ ok: true, ts: new Date().toISOString() }));

app.get('/', (req, res) => res.redirect('/teams/'));

app.use(express.static(__dirname));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`ia-projetos running on :${PORT}`));
