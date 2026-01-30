/**
 * API Routes - Calculadora Reembolso KM
 * Endpoints para salvar resultados e usuarios
 */

const express = require('express');
const router = express.Router();
const { supabase } = require('../services/supabase');

// Tables
const TABLE_USUARIOS = 'growth_calculadora_usuarios';
const TABLE_RESULTADOS = 'growth_calculadora_resultados';

/**
 * POST /api/resultado
 * Salva um resultado de calculo
 *
 * Body: {
 *   cookie_id: string (required),
 *   km_percorrido: number (required),
 *   preco_combustivel: number,
 *   consumo_medio: number,
 *   valor_reembolso: number (required),
 *   tipo_veiculo: string,
 *   dados_completos: object
 * }
 */
router.post('/resultado', async (req, res) => {
  try {
    const {
      cookie_id,
      km_percorrido,
      preco_combustivel,
      consumo_medio,
      valor_reembolso,
      tipo_veiculo,
      dados_completos
    } = req.body;

    // Validation
    const missingFields = [];
    if (!cookie_id) missingFields.push('cookie_id');
    if (km_percorrido === undefined || km_percorrido === null) missingFields.push('km_percorrido');
    if (valor_reembolso === undefined || valor_reembolso === null) missingFields.push('valor_reembolso');

    if (missingFields.length > 0) {
      return res.status(400).json({
        error: `Campos obrigatorios ausentes: ${missingFields.join(', ')}`
      });
    }

    // Insert into Supabase
    const { data, error } = await supabase
      .from(TABLE_RESULTADOS)
      .insert({
        cookie_id,
        km_percorrido,
        preco_combustivel,
        consumo_medio,
        valor_reembolso,
        tipo_veiculo,
        dados_completos
      })
      .select()
      .single();

    if (error) {
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Erro ao salvar resultado' });
    }

    return res.status(201).json({
      id: data.id,
      created_at: data.created_at
    });
  } catch (err) {
    console.error('Error in POST /api/resultado:', err);
    return res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

/**
 * POST /api/usuario
 * Cria ou atualiza um usuario
 * Se telefone ja existe, atualiza o cookie_id
 *
 * Body: {
 *   nome: string,
 *   telefone: string (required),
 *   nome_empresa: string,
 *   cookie_id: string (required)
 * }
 */
router.post('/usuario', async (req, res) => {
  try {
    const { nome, telefone, nome_empresa, cookie_id } = req.body;

    // Validation
    const missingFields = [];
    if (!telefone) missingFields.push('telefone');
    if (!cookie_id) missingFields.push('cookie_id');

    if (missingFields.length > 0) {
      return res.status(400).json({
        error: `Campos obrigatorios ausentes: ${missingFields.join(', ')}`
      });
    }

    // Upsert: insert or update on conflict (telefone)
    const insertData = {
      telefone,
      cookie_id
    };

    // Campos opcionais - serão ignorados se a coluna não existir
    if (nome) {
      insertData.nome = nome;
    }

    if (nome_empresa) {
      insertData.nome_empresa = nome_empresa;
    }

    // Tenta inserir com todos os campos
    let { data, error } = await supabase
      .from(TABLE_USUARIOS)
      .upsert(insertData, { onConflict: 'telefone' })
      .select()
      .single();

    // Se erro por coluna nome não existir, tenta sem o campo nome
    if (error && error.code === 'PGRST204' && error.message.includes('nome')) {
      delete insertData.nome;
      const retry = await supabase
        .from(TABLE_USUARIOS)
        .upsert(insertData, { onConflict: 'telefone' })
        .select()
        .single();
      data = retry.data;
      error = retry.error;
    }

    if (error) {
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Erro ao salvar usuario' });
    }

    return res.status(201).json({
      id: data.id,
      created_at: data.created_at
    });
  } catch (err) {
    console.error('Error in POST /api/usuario:', err);
    return res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

/**
 * GET /api/contador
 * Retorna total de calculos realizados
 */
router.get('/contador', async (req, res) => {
  try {
    const { count, error } = await supabase
      .from(TABLE_RESULTADOS)
      .select('*', { count: 'exact', head: true });

    if (error) {
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Erro ao buscar contador' });
    }

    return res.status(200).json({
      total: count || 0
    });
  } catch (err) {
    console.error('Error in GET /api/contador:', err);
    return res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

/**
 * GET /api/historico
 * Retorna historico de resultados
 *
 * Query params:
 *   cookie_id: string (optional)
 *   telefone: string (optional)
 *
 * Pelo menos um dos params e obrigatorio
 */
router.get('/historico', async (req, res) => {
  try {
    const { cookie_id, telefone } = req.query;

    // Validation
    if (!cookie_id && !telefone) {
      return res.status(400).json({
        error: 'Informe cookie_id ou telefone para buscar o historico'
      });
    }

    let usuario = null;
    let resultados = [];
    let searchCookieId = cookie_id;

    // If telefone provided, first find the user
    if (telefone) {
      const { data: userData, error: userError } = await supabase
        .from(TABLE_USUARIOS)
        .select('*')
        .eq('telefone', telefone)
        .single();

      if (!userError && userData) {
        usuario = userData;
        searchCookieId = userData.cookie_id;
      }
    } else if (cookie_id) {
      // Search user by cookie_id
      const { data: userData, error: userError } = await supabase
        .from(TABLE_USUARIOS)
        .select('*')
        .eq('cookie_id', cookie_id)
        .single();

      if (!userError && userData) {
        usuario = userData;
      }
    }

    // Get results by cookie_id
    if (searchCookieId) {
      const { data: resultData, error: resultError } = await supabase
        .from(TABLE_RESULTADOS)
        .select('*')
        .eq('cookie_id', searchCookieId)
        .order('created_at', { ascending: false });

      if (!resultError && resultData) {
        resultados = resultData;
      }
    }

    return res.status(200).json({
      usuario,
      resultados
    });
  } catch (err) {
    console.error('Error in GET /api/historico:', err);
    return res.status(500).json({ error: 'Erro interno do servidor' });
  }
});

module.exports = router;
