// db.js — SQLite setup, schema e queries (usando sqlite3 async)
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const DB_PATH = process.env.DB_PATH || path.join(__dirname, 'data', 'portal.db');
const dbDir = path.dirname(DB_PATH);
if (!fs.existsSync(dbDir)) fs.mkdirSync(dbDir, { recursive: true });

const db = new sqlite3.Database(DB_PATH);

// Schema
db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS posts (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      title        TEXT NOT NULL,
      slug         TEXT UNIQUE NOT NULL,
      content_html TEXT NOT NULL,
      excerpt      TEXT DEFAULT '',
      image_url    TEXT DEFAULT '',
      video_id     TEXT DEFAULT '',
      category     TEXT DEFAULT 'videos',
      status       TEXT DEFAULT 'pending',
      created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
      published_at DATETIME
    )
  `);

  db.run(`
    CREATE TABLE IF NOT EXISTS subscribers (
      id           INTEGER PRIMARY KEY AUTOINCREMENT,
      email        TEXT UNIQUE NOT NULL,
      active       INTEGER DEFAULT 1,
      confirmed    INTEGER DEFAULT 0,
      confirm_token TEXT,
      created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Migração: adicionar colunas em bancos existentes
  db.run(`ALTER TABLE subscribers ADD COLUMN confirmed INTEGER DEFAULT 0`, () => {});
  db.run(`ALTER TABLE subscribers ADD COLUMN confirm_token TEXT`, () => {});

  db.run(`
    CREATE TABLE IF NOT EXISTS comments (
      id         INTEGER PRIMARY KEY AUTOINCREMENT,
      post_id    INTEGER NOT NULL,
      post_slug  TEXT NOT NULL,
      author     TEXT NOT NULL,
      content    TEXT NOT NULL,
      status     TEXT DEFAULT 'pending',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (post_id) REFERENCES posts(id)
    )
  `);

  db.run(`
    CREATE INDEX IF NOT EXISTS idx_posts_published
    ON posts (published_at DESC)
    WHERE status = 'published'
  `);

  db.run(`
    CREATE INDEX IF NOT EXISTS idx_posts_category_published
    ON posts (category, published_at DESC)
    WHERE status = 'published'
  `);
});

// Helpers promisificados
const run = (sql, params = []) => new Promise((resolve, reject) => {
  db.run(sql, params, function (err) {
    if (err) reject(err);
    else resolve({ lastID: this.lastID, changes: this.changes });
  });
});

const all = (sql, params = []) => new Promise((resolve, reject) => {
  db.all(sql, params, (err, rows) => err ? reject(err) : resolve(rows));
});

const get = (sql, params = []) => new Promise((resolve, reject) => {
  db.get(sql, params, (err, row) => err ? reject(err) : resolve(row));
});

module.exports = {
  // --- Posts ---
  getPublished: (limit = 20, offset = 0, category = null) => {
    if (category) {
      return all("SELECT * FROM posts WHERE status = 'published' AND category = ? ORDER BY published_at DESC LIMIT ? OFFSET ?", [category, limit, offset]);
    }
    return all("SELECT * FROM posts WHERE status = 'published' ORDER BY published_at DESC LIMIT ? OFFSET ?", [limit, offset]);
  },

  getRecentPublished: (limit = 5) =>
    all("SELECT * FROM posts WHERE status = 'published' ORDER BY published_at DESC LIMIT ?", [limit]),

  getBySlug: (slug) =>
    get("SELECT * FROM posts WHERE slug = ? AND status = 'published'", [slug]),

  getByVideoId: (video_id) =>
    get("SELECT id FROM posts WHERE video_id = ?", [video_id]),

  getAll: () =>
    all("SELECT * FROM posts ORDER BY created_at DESC"),

  createPost: (data) =>
    run(
      `INSERT INTO posts (title, slug, content_html, excerpt, image_url, video_id, category, status)
       VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')`,
      [data.title, data.slug, data.content_html, data.excerpt || '', data.image_url || '', data.video_id || '', data.category || 'videos']
    ),

  publish: (id) =>
    run("UPDATE posts SET status = 'published', published_at = CURRENT_TIMESTAMP WHERE id = ?", [id]),

  reject: (id) =>
    run("UPDATE posts SET status = 'rejected' WHERE id = ?", [id]),

  updatePost: (id, data) =>
    run(
      `UPDATE posts SET title = ?, excerpt = ?, content_html = ?, category = ? WHERE id = ?`,
      [data.title, data.excerpt || '', data.content_html, data.category || 'videos', id]
    ),

  deletePost: (id) =>
    run("DELETE FROM posts WHERE id = ?", [id]),

  // --- Newsletter ---
  subscribe: (email) =>
    run("INSERT INTO subscribers (email) VALUES (?)", [email]),

  unsubscribe: (email) =>
    run("UPDATE subscribers SET active = 0 WHERE email = ?", [email]),

  confirmSubscriber: (token) =>
    run("UPDATE subscribers SET confirmed = 1, confirm_token = NULL WHERE confirm_token = ?", [token]),

  getConfirmedSubscribers: () =>
    all("SELECT * FROM subscribers WHERE active = 1 AND confirmed = 1"),

  setConfirmToken: (email, token) =>
    run("UPDATE subscribers SET confirm_token = ? WHERE email = ?", [token, email]),

  getActiveSubscribers: () =>
    all("SELECT * FROM subscribers WHERE active = 1"),

  // --- Comentários ---
  createComment: (data) =>
    run(
      "INSERT INTO comments (post_id, post_slug, author, content, status) VALUES (?, ?, ?, ?, 'pending')",
      [data.post_id, data.post_slug, data.author, data.content]
    ),

  getApprovedComments: (post_slug) =>
    all("SELECT * FROM comments WHERE post_slug = ? AND status = 'approved' ORDER BY created_at ASC", [post_slug]),

  getPendingComments: () =>
    all("SELECT * FROM comments WHERE status = 'pending' ORDER BY created_at DESC"),

  getAllComments: () =>
    all("SELECT * FROM comments ORDER BY created_at DESC"),

  approveComment: (id) =>
    run("UPDATE comments SET status = 'approved' WHERE id = ?", [id]),

  rejectComment: (id) =>
    run("UPDATE comments SET status = 'rejected' WHERE id = ?", [id]),

  search: (q, limit = 10) => {
    const term = `%${q}%`;
    return all(
      "SELECT * FROM posts WHERE status = 'published' AND (title LIKE ? OR excerpt LIKE ?) ORDER BY published_at DESC LIMIT ?",
      [term, term, limit]
    );
  },

  getRelated: (slug, category, limit = 3) =>
    all(
      "SELECT * FROM posts WHERE status = 'published' AND category = ? AND slug != ? ORDER BY published_at DESC LIMIT ?",
      [category, slug, limit]
    ),
};
