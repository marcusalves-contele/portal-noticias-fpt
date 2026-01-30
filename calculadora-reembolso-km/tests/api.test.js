/**
 * API Tests - Calculadora Reembolso KM
 * TDD: Tests written FIRST, then implementation
 */

const request = require('supertest');

// Mock data storage
const mockData = {
  usuarios: [],
  resultados: []
};

// Mock Supabase before importing app
jest.mock('../src/services/supabase', () => {
  return {
    supabase: {
      from: jest.fn((table) => {
        return {
          insert: jest.fn((data) => ({
            select: jest.fn(() => ({
              single: jest.fn(async () => {
                const newRecord = {
                  ...data,
                  id: `mock-id-${Date.now()}-${Math.random()}`,
                  created_at: new Date().toISOString()
                };
                if (table === 'growth_calculadora_usuarios') {
                  mockData.usuarios.push(newRecord);
                } else if (table === 'growth_calculadora_resultados') {
                  mockData.resultados.push(newRecord);
                }
                return { data: newRecord, error: null };
              })
            }))
          })),
          select: jest.fn(() => ({
            eq: jest.fn((field, value) => ({
              single: jest.fn(async () => {
                let found = null;
                if (table === 'growth_calculadora_usuarios') {
                  found = mockData.usuarios.find(u => u[field] === value);
                }
                return {
                  data: found || null,
                  error: found ? null : { code: 'PGRST116' }
                };
              }),
              order: jest.fn(async () => {
                let results = [];
                if (table === 'growth_calculadora_resultados') {
                  results = mockData.resultados.filter(r => r[field] === value);
                }
                return { data: results, error: null };
              })
            }))
          })),
          upsert: jest.fn((data) => ({
            select: jest.fn(() => ({
              single: jest.fn(async () => {
                const existing = mockData.usuarios.find(u => u.telefone === data.telefone);
                if (existing) {
                  Object.assign(existing, data);
                  return { data: existing, error: null };
                }
                const newRecord = {
                  ...data,
                  id: `mock-id-${Date.now()}-${Math.random()}`,
                  created_at: new Date().toISOString()
                };
                mockData.usuarios.push(newRecord);
                return { data: newRecord, error: null };
              })
            }))
          }))
        };
      })
    },
    _mockData: mockData,
    _resetMockData: () => {
      mockData.usuarios = [];
      mockData.resultados = [];
    }
  };
});

const app = require('../src/server');
const { _resetMockData } = require('../src/services/supabase');

describe('API Calculadora Reembolso KM', () => {
  beforeEach(() => {
    _resetMockData();
  });

  // ============================================
  // GET /health
  // ============================================
  describe('GET /health', () => {
    it('should return status ok', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toEqual({ status: 'ok' });
    });
  });

  // ============================================
  // POST /api/resultado
  // ============================================
  describe('POST /api/resultado', () => {
    it('should create a new resultado with valid data', async () => {
      const payload = {
        cookie_id: 'test-cookie-123',
        km_percorrido: 150.5,
        preco_combustivel: 5.89,
        consumo_medio: 12,
        valor_reembolso: 73.65,
        tipo_veiculo: 'carro',
        dados_completos: {
          km_diario: 50,
          dias_trabalhados: 22
        }
      };

      const response = await request(app)
        .post('/api/resultado')
        .send(payload)
        .expect(201);

      expect(response.body).toHaveProperty('id');
      expect(response.body).toHaveProperty('created_at');
    });

    it('should return 400 if cookie_id is missing', async () => {
      const payload = {
        km_percorrido: 150.5,
        valor_reembolso: 73.65
      };

      const response = await request(app)
        .post('/api/resultado')
        .send(payload)
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('cookie_id');
    });

    it('should return 400 if km_percorrido is missing', async () => {
      const payload = {
        cookie_id: 'test-cookie-123',
        valor_reembolso: 73.65
      };

      const response = await request(app)
        .post('/api/resultado')
        .send(payload)
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('km_percorrido');
    });

    it('should return 400 if valor_reembolso is missing', async () => {
      const payload = {
        cookie_id: 'test-cookie-123',
        km_percorrido: 150.5
      };

      const response = await request(app)
        .post('/api/resultado')
        .send(payload)
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('valor_reembolso');
    });

    it('should accept optional fields', async () => {
      const payload = {
        cookie_id: 'test-cookie-456',
        km_percorrido: 200,
        valor_reembolso: 100
        // Optional fields omitted
      };

      const response = await request(app)
        .post('/api/resultado')
        .send(payload)
        .expect(201);

      expect(response.body).toHaveProperty('id');
    });
  });

  // ============================================
  // POST /api/usuario
  // ============================================
  describe('POST /api/usuario', () => {
    it('should create a new usuario with valid data', async () => {
      const payload = {
        telefone: '11999887766',
        nome_empresa: 'Empresa Teste LTDA',
        cookie_id: 'test-cookie-789'
      };

      const response = await request(app)
        .post('/api/usuario')
        .send(payload)
        .expect(201);

      expect(response.body).toHaveProperty('id');
      expect(response.body).toHaveProperty('created_at');
    });

    it('should return 400 if telefone is missing', async () => {
      const payload = {
        nome_empresa: 'Empresa Teste',
        cookie_id: 'test-cookie-789'
      };

      const response = await request(app)
        .post('/api/usuario')
        .send(payload)
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('telefone');
    });

    it('should return 400 if cookie_id is missing', async () => {
      const payload = {
        telefone: '11999887766',
        nome_empresa: 'Empresa Teste'
      };

      const response = await request(app)
        .post('/api/usuario')
        .send(payload)
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('cookie_id');
    });

    it('should update cookie_id if telefone already exists', async () => {
      // First create
      await request(app)
        .post('/api/usuario')
        .send({
          telefone: '11999887766',
          nome_empresa: 'Empresa Original',
          cookie_id: 'old-cookie'
        })
        .expect(201);

      // Second call with same telefone should update
      const response = await request(app)
        .post('/api/usuario')
        .send({
          telefone: '11999887766',
          nome_empresa: 'Empresa Atualizada',
          cookie_id: 'new-cookie'
        })
        .expect(201);

      expect(response.body).toHaveProperty('id');
    });

    it('should accept nome_empresa as optional', async () => {
      const payload = {
        telefone: '11888776655',
        cookie_id: 'test-cookie-no-empresa'
      };

      const response = await request(app)
        .post('/api/usuario')
        .send(payload)
        .expect(201);

      expect(response.body).toHaveProperty('id');
    });
  });

  // ============================================
  // GET /api/historico
  // ============================================
  describe('GET /api/historico', () => {
    it('should return 400 if no query params provided', async () => {
      const response = await request(app)
        .get('/api/historico')
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error).toContain('cookie_id');
    });

    it('should return historico by cookie_id', async () => {
      const response = await request(app)
        .get('/api/historico')
        .query({ cookie_id: 'test-cookie-123' })
        .expect(200);

      expect(response.body).toHaveProperty('usuario');
      expect(response.body).toHaveProperty('resultados');
      expect(Array.isArray(response.body.resultados)).toBe(true);
    });

    it('should return historico by telefone', async () => {
      const response = await request(app)
        .get('/api/historico')
        .query({ telefone: '11999887766' })
        .expect(200);

      expect(response.body).toHaveProperty('usuario');
      expect(response.body).toHaveProperty('resultados');
    });

    it('should return empty resultados if no data found', async () => {
      const response = await request(app)
        .get('/api/historico')
        .query({ cookie_id: 'nonexistent-cookie' })
        .expect(200);

      expect(response.body.resultados).toEqual([]);
    });
  });

  // ============================================
  // Error handling
  // ============================================
  describe('Error Handling', () => {
    it('should return 404 for unknown routes', async () => {
      const response = await request(app)
        .get('/api/unknown')
        .expect(404);

      expect(response.body).toHaveProperty('error');
    });

    it('should handle invalid JSON body', async () => {
      const response = await request(app)
        .post('/api/resultado')
        .set('Content-Type', 'application/json')
        .send('{ invalid json }')
        .expect(400);

      expect(response.body).toHaveProperty('error');
    });
  });

  // ============================================
  // CORS
  // ============================================
  describe('CORS', () => {
    it('should include CORS headers', async () => {
      const response = await request(app)
        .get('/health')
        .set('Origin', 'http://localhost:3000')
        .expect(200);

      expect(response.headers).toHaveProperty('access-control-allow-origin');
    });

    it('should handle OPTIONS preflight', async () => {
      const response = await request(app)
        .options('/api/resultado')
        .set('Origin', 'http://localhost:3000')
        .expect(204);

      expect(response.headers).toHaveProperty('access-control-allow-methods');
    });
  });
});
