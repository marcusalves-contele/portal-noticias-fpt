const express = require('express');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// ---------------------------------------------------------------------------
// SEO helpers
// ---------------------------------------------------------------------------

const DOMAIN_BR = 'https://contele.com.br';
const DOMAIN_EN = 'https://contele.io';

function getDomains(req) {
  const host = req.hostname || '';
  const isEN = host.includes('contele.io');
  const self = isEN ? DOMAIN_EN : DOMAIN_BR;
  const alt  = isEN ? DOMAIN_BR : DOMAIN_EN;
  const selfLang = isEN ? 'en' : 'pt-br';
  const altLang  = isEN ? 'pt-br' : 'en';
  return { self, alt, selfLang, altLang };
}

/**
 * Reads an HTML file, rewrites canonical to match the serving domain,
 * and injects hreflang tags. Sends the result as response.
 */
function sendHtmlWithSeo(req, res, filePath) {
  const { self, alt, selfLang, altLang } = getDomains(req);
  const urlPath = req.path === '/' ? '/' : req.path;
  const canonicalUrl = self + urlPath;

  fs.readFile(filePath, 'utf8', (err, html) => {
    if (err) {
      return res.status(500).send('Internal Server Error');
    }

    // 1. Replace existing canonical (any domain) with correct one
    html = html.replace(
      /<link\s+rel="canonical"\s+href="[^"]*"\s*\/?>/i,
      `<link rel="canonical" href="${canonicalUrl}">`
    );

    // If no canonical existed, inject one before </head>
    if (!html.includes('rel="canonical"')) {
      html = html.replace(
        '</head>',
        `  <link rel="canonical" href="${canonicalUrl}">\n</head>`
      );
    }

    // 2. Remove any existing hreflang tags (safety)
    html = html.replace(/<link\s+rel="alternate"\s+hreflang="[^"]*"\s+href="[^"]*"\s*\/?>\n?/gi, '');

    // 3. Inject hreflang tags right after canonical
    const hreflangTags = [
      `<link rel="alternate" hreflang="${selfLang}" href="${self}${urlPath}">`,
      `<link rel="alternate" hreflang="${altLang}" href="${alt}${urlPath}">`,
      `<link rel="alternate" hreflang="x-default" href="${DOMAIN_EN}${urlPath}">`
    ].join('\n  ');

    html = html.replace(
      /<link\s+rel="canonical"\s+href="[^"]*">/i,
      (match) => `${match}\n  ${hreflangTags}`
    );

    // 4. Fix og:url to match canonical
    html = html.replace(
      /<meta\s+property="og:url"\s+content="[^"]*"\s*\/?>/i,
      `<meta property="og:url" content="${canonicalUrl}">`
    );

    res.type('html').send(html);
  });
}

// ---------------------------------------------------------------------------
// Dynamic robots.txt (per domain)
// ---------------------------------------------------------------------------
app.get('/robots.txt', (req, res) => {
  const { self } = getDomains(req);
  const content = [
    'User-agent: *',
    'Allow: /',
    '',
    `Sitemap: ${self}/sitemap.xml`
  ].join('\n');
  res.type('text').send(content);
});

// ---------------------------------------------------------------------------
// Dynamic sitemap.xml (per domain)
// ---------------------------------------------------------------------------
const PAGES = ['/', '/privacy'];

app.get('/sitemap.xml', (req, res) => {
  const { self, alt, selfLang, altLang } = getDomains(req);
  const today = new Date().toISOString().slice(0, 10);

  const urls = PAGES.map((pg) => {
    const loc = self + pg;
    const altLoc = alt + pg;
    const priority = pg === '/' ? '1.0' : '0.5';
    const changefreq = pg === '/' ? 'weekly' : 'monthly';
    return `  <url>
    <loc>${loc}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
    <xhtml:link rel="alternate" hreflang="${selfLang}" href="${loc}"/>
    <xhtml:link rel="alternate" hreflang="${altLang}" href="${altLoc}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="${DOMAIN_EN}${pg}"/>
  </url>`;
  }).join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls}
</urlset>`;

  res.type('application/xml').send(xml);
});

// ---------------------------------------------------------------------------
// Static assets (images, CSS, JS, fonts — NOT html/robots/sitemap)
// ---------------------------------------------------------------------------
app.use(express.static(path.join(__dirname, 'public'), {
  // Let our explicit routes handle these
  index: false,
  extensions: []
}));

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

// Home: detect domain to serve pt-BR or en
app.get('/', (req, res) => {
  const host = req.hostname || '';
  if (host.includes('contele.io')) {
    sendHtmlWithSeo(req, res, path.join(__dirname, 'public', 'index-en.html'));
  } else {
    sendHtmlWithSeo(req, res, path.join(__dirname, 'public', 'index.html'));
  }
});

// Preview da nova pagina (manter temporariamente)
app.get('/nova', (req, res) => {
  sendHtmlWithSeo(req, res, path.join(__dirname, 'public', 'index.html'));
});

// Versao ingles acessivel diretamente
app.get('/en', (req, res) => {
  sendHtmlWithSeo(req, res, path.join(__dirname, 'public', 'index-en.html'));
});

// Privacidade
app.get('/privacy', (req, res) => {
  sendHtmlWithSeo(req, res, path.join(__dirname, 'public', 'privacy.html'));
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
