// server.js
const express = require('express');
const cors = require('cors');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');

const app = express();
const PORT = 3000;
const JWT_SECRET = 'finoraqi_secret_key_2026';

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Banco de dados SQLite
const db = new sqlite3.Database('./finoraqi.db');

// Criar tabelas
db.serialize(() => {
db.run(`CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
nome TEXT NOT NULL,
email TEXT UNIQUE NOT NULL,
senha TEXT NOT NULL,
telefone TEXT,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)`);

db.run(`CREATE TABLE IF NOT EXISTS transactions (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
type TEXT NOT NULL,
amount REAL NOT NULL,
category TEXT,
description TEXT,
date DATE,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY(user_id) REFERENCES users(id)
)`);

db.run(`CREATE TABLE IF NOT EXISTS investments (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
name TEXT NOT NULL,
amount REAL NOT NULL,
rate REAL,
type TEXT,
date DATE,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY(user_id) REFERENCES users(id)
)`);

db.run(`CREATE TABLE IF NOT EXISTS goals (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
name TEXT NOT NULL,
target REAL NOT NULL,
saved REAL DEFAULT 0,
deadline DATE,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY(user_id) REFERENCES users(id)
)`);

db.run(`CREATE TABLE IF NOT EXISTS wallets (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
name TEXT NOT NULL,
type TEXT,
balance REAL DEFAULT 0,
rate REAL,
institution TEXT,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
FOREIGN KEY(user_id) REFERENCES users(id)
)`);
});

// Middleware de autenticação
function authenticateToken(req, res, next) {
const authHeader = req.headers['authorization'];
const token = authHeader && authHeader.split(' ')[1];

if (!token) {
return res.status(401).json({ error: 'Token não fornecido' });
}

jwt.verify(token, JWT_SECRET, (err, user) => {
if (err) {
return res.status(403).json({ error: 'Token inválido' });
}
req.user = user;
next();
});
}

// Rotas de Autenticação
app.post('/api/auth/register', async (req, res) => {
const { nome, email, telefone, password } = req.body;

try {
const hashedPassword = await bcrypt.hash(password, 10);

db.run(
'INSERT INTO users (nome, email, senha, telefone) VALUES (?, ?, ?, ?)',
[nome, email, hashedPassword, telefone],
function(err) {
if (err) {
if (err.message.includes('UNIQUE')) {
return res.status(400).json({ error: 'Email já cadastrado' });
}
return res.status(500).json({ error: 'Erro ao criar usuário' });
}

const token = jwt.sign({ id: this.lastID, email }, JWT_SECRET, { expiresIn: '24h' });

res.status(201).json({
message: 'Usuário criado com sucesso',
token,
user: { id: this.lastID, nome, email, telefone }
});
}
);
} catch (error) {
res.status(500).json({ error: 'Erro no servidor' });
}
});

app.post('/api/auth/login', (req, res) => {
const { email, password } = req.body;

db.get('SELECT * FROM users WHERE email = ?', [email], async (err, user) => {
if (err) {
return res.status(500).json({ error: 'Erro no servidor' });
}

if (!user) {
return res.status(401).json({ error: 'Email ou senha inválidos' });
}

const validPassword = await bcrypt.compare(password, user.senha);
if (!validPassword) {
return res.status(401).json({ error: 'Email ou senha inválidos' });
}

const token = jwt.sign({ id: user.id, email: user.email }, JWT_SECRET, { expiresIn: '24h' });

res.json({
message: 'Login realizado com sucesso',
token,
user: { id: user.id, nome: user.nome, email: user.email, telefone: user.telefone }
});
});
});

// Rotas de Transações
app.get('/api/transactions', authenticateToken, (req, res) => {
db.all('SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC', [req.user.id], (err, rows) => {
if (err) {
return res.status(500).json({ error: 'Erro ao buscar transações' });
}
res.json(rows);
});
});

app.post('/api/transactions', authenticateToken, (req, res) => {
const { type, amount, category, description, date } = req.body;

db.run(
'INSERT INTO transactions (user_id, type, amount, category, description, date) VALUES (?, ?, ?, ?, ?, ?)',
[req.user.id, type, amount, category, description, date],
function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao criar transação' });
}
res.status(201).json({ id: this.lastID, user_id: req.user.id, type, amount, category, description, date });
}
);
});

app.put('/api/transactions/:id', authenticateToken, (req, res) => {
const { type, amount, category, description, date } = req.body;
const { id } = req.params;

db.run(
'UPDATE transactions SET type = ?, amount = ?, category = ?, description = ?, date = ? WHERE id = ? AND user_id = ?',
[type, amount, category, description, date, id, req.user.id],
function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao atualizar transação' });
}
if (this.changes === 0) {
return res.status(404).json({ error: 'Transação não encontrada' });
}
res.json({ message: 'Transação atualizada' });
}
);
});

app.delete('/api/transactions/:id', authenticateToken, (req, res) => {
const { id } = req.params;

db.run('DELETE FROM transactions WHERE id = ? AND user_id = ?', [id, req.user.id], function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao excluir transação' });
}
if (this.changes === 0) {
return res.status(404).json({ error: 'Transação não encontrada' });
}
res.json({ message: 'Transação excluída' });
});
});

// Rotas de Investimentos
app.get('/api/investments', authenticateToken, (req, res) => {
db.all('SELECT * FROM investments WHERE user_id = ? ORDER BY date DESC', [req.user.id], (err, rows) => {
if (err) {
return res.status(500).json({ error: 'Erro ao buscar investimentos' });
}
res.json(rows);
});
});

app.post('/api/investments', authenticateToken, (req, res) => {
const { name, amount, rate, type, date } = req.body;

db.run(
'INSERT INTO investments (user_id, name, amount, rate, type, date) VALUES (?, ?, ?, ?, ?, ?)',
[req.user.id, name, amount, rate, type, date],
function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao criar investimento' });
}
res.status(201).json({ id: this.lastID, user_id: req.user.id, name, amount, rate, type, date });
}
);
});

// Rotas de Metas
app.get('/api/goals', authenticateToken, (req, res) => {
db.all('SELECT * FROM goals WHERE user_id = ? ORDER BY deadline', [req.user.id], (err, rows) => {
if (err) {
return res.status(500).json({ error: 'Erro ao buscar metas' });
}
res.json(rows);
});
});

app.post('/api/goals', authenticateToken, (req, res) => {
const { name, target, saved, deadline } = req.body;

db.run(
'INSERT INTO goals (user_id, name, target, saved, deadline) VALUES (?, ?, ?, ?, ?)',
[req.user.id, name, target, saved || 0, deadline],
function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao criar meta' });
}
res.status(201).json({ id: this.lastID, user_id: req.user.id, name, target, saved: saved || 0, deadline });
}
);
});

app.put('/api/goals/:id', authenticateToken, (req, res) => {
const { name, target, saved, deadline } = req.body;
const { id } = req.params;

db.run(
'UPDATE goals SET name = ?, target = ?, saved = ?, deadline = ? WHERE id = ? AND user_id = ?',
[name, target, saved, deadline, id, req.user.id],
function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao atualizar meta' });
}
if (this.changes === 0) {
return res.status(404).json({ error: 'Meta não encontrada' });
}
res.json({ message: 'Meta atualizada' });
}
);
});

app.delete('/api/goals/:id', authenticateToken, (req, res) => {
const { id } = req.params;

db.run('DELETE FROM goals WHERE id = ? AND user_id = ?', [id, req.user.id], function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao excluir meta' });
}
if (this.changes === 0) {
return res.status(404).json({ error: 'Meta não encontrada' });
}
res.json({ message: 'Meta excluída' });
});
});

// Rotas de Carteiras
app.get('/api/wallets', authenticateToken, (req, res) => {
db.all('SELECT * FROM wallets WHERE user_id = ? ORDER BY created_at DESC', [req.user.id], (err, rows) => {
if (err) {
return res.status(500).json({ error: 'Erro ao buscar carteiras' });
}
res.json(rows);
});
});

app.post('/api/wallets', authenticateToken, (req, res) => {
const { name, type, balance, rate, institution } = req.body;

db.run(
'INSERT INTO wallets (user_id, name, type, balance, rate, institution) VALUES (?, ?, ?, ?, ?, ?)',
[req.user.id, name, type, balance || 0, rate || 0, institution],
function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao criar carteira' });
}
res.status(201).json({ id: this.lastID, user_id: req.user.id, name, type, balance: balance || 0, rate: rate || 0, institution });
}
);
});

// Rota de Perfil
app.get('/api/profile', authenticateToken, (req, res) => {
db.get('SELECT id, nome, email, telefone, created_at FROM users WHERE id = ?', [req.user.id], (err, user) => {
if (err) {
return res.status(500).json({ error: 'Erro ao buscar perfil' });
}
if (!user) {
return res.status(404).json({ error: 'Usuário não encontrado' });
}
res.json(user);
});
});

app.put('/api/profile', authenticateToken, (req, res) => {
const { nome, telefone } = req.body;

db.run('UPDATE users SET nome = ?, telefone = ? WHERE id = ?', [nome, telefone, req.user.id], function(err) {
if (err) {
return res.status(500).json({ error: 'Erro ao atualizar perfil' });
}
res.json({ message: 'Perfil atualizado', nome, telefone });
});
});

// Iniciar servidor
app.listen(PORT, () => {
console.log(` Servidor FinoraQi rodando em http://localhost:${PORT}`);
});
