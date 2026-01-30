/**
 * Supabase Client Service
 * Conexao com Supabase para persistencia de dados
 */

const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const supabaseUrl = process.env.SUPABASE_URL || 'https://ziddmmazfgydnvcrjjtq.supabase.co';
const supabaseKey = process.env.SUPABASE_ANON_KEY;

if (!supabaseKey) {
  console.warn('Warning: SUPABASE_ANON_KEY not set. Database operations will fail.');
}

const supabase = createClient(supabaseUrl, supabaseKey || 'dummy-key-for-testing');

module.exports = { supabase };
