/**
 * Calculadora Reembolso KM - Frontend App
 * Integra com API para salvar resultados e capturar leads
 */

(function() {
    'use strict';

    // ==========================================
    // CONFIG
    // ==========================================
    const CONFIG = {
        API_BASE: '', // Relativo - mesmo servidor
        STORAGE_KEY: 'calc_reembolso_km'
    };

    // ==========================================
    // CUSTOS POR CATEGORIA DE VEÍCULO (R$/km)
    // Baseado em pesquisa 2025 - Valores conservadores e equilibrados
    // Premissas: Depreciação 10%/ano (carro usado), 18.000 km/ano, 50% proporcionalidade
    // ==========================================
    const VEHICLE_COSTS = {
        moto: {
            // Moto 150cc, valor médio R$ 20k
            depreciacao: 0.06,      // R$ 20k × 10% × 50% ÷ 18k km
            seguro: 0.03,           // R$ 1.2k × 50% ÷ 18k km
            custos_fixos: 0.06,     // Combo: Manutenção + Pneus + IPVA
            total_fixo: 0.15,
            consumo_default: 35.0,
            valor_medio: 20000
        },
        carro_popular: {
            // Carro popular, valor médio R$ 70k
            depreciacao: 0.19,      // R$ 70k × 10% × 50% ÷ 18k km
            seguro: 0.07,           // R$ 2.5k × 50% ÷ 18k km
            custos_fixos: 0.19,     // Combo: Manutenção + Pneus + IPVA
            total_fixo: 0.45,
            consumo_default: 12.0,
            valor_medio: 70000
        },
        carro_medio: {
            // Carro médio, valor médio R$ 120k
            depreciacao: 0.33,      // R$ 120k × 10% × 50% ÷ 18k km
            seguro: 0.11,           // R$ 4k × 50% ÷ 18k km
            custos_fixos: 0.26,     // Combo: Manutenção + Pneus + IPVA
            total_fixo: 0.70,
            consumo_default: 10.0,
            valor_medio: 120000
        },
        carro_suv: {
            // SUV/Pickup, valor médio R$ 180k
            depreciacao: 0.50,      // R$ 180k × 10% × 50% ÷ 18k km
            seguro: 0.15,           // R$ 6k × 50% ÷ 18k km
            custos_fixos: 0.35,     // Combo: Manutenção + Pneus + IPVA
            total_fixo: 1.00,
            consumo_default: 8.0,
            valor_medio: 180000
        }
    };

    // ==========================================
    // STORAGE & COOKIE ID
    // ==========================================
    function getCookieId() {
        let data = getStorageData();
        if (!data.cookie_id) {
            data.cookie_id = generateUUID();
            saveStorageData(data);
        }
        return data.cookie_id;
    }

    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    function getStorageData() {
        try {
            const data = localStorage.getItem(CONFIG.STORAGE_KEY);
            return data ? JSON.parse(data) : {};
        } catch (e) {
            return {};
        }
    }

    function saveStorageData(data) {
        try {
            localStorage.setItem(CONFIG.STORAGE_KEY, JSON.stringify(data));
        } catch (e) {
            console.warn('Nao foi possivel salvar no localStorage');
        }
    }

    function getUserPhone() {
        return getStorageData().telefone || null;
    }

    function setUserPhone(telefone) {
        const data = getStorageData();
        data.telefone = telefone;
        saveStorageData(data);
    }

    // ==========================================
    // FORMATTERS
    // ==========================================
    function formatMoney(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    }

    function formatPhone(value) {
        // Remove tudo que nao for numero
        const digits = value.replace(/\D/g, '');

        // Formata (XX) XXXXX-XXXX
        if (digits.length <= 2) {
            return digits;
        } else if (digits.length <= 7) {
            return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
        } else if (digits.length <= 11) {
            return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
        } else {
            return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
        }
    }

    function cleanPhone(value) {
        return value.replace(/\D/g, '');
    }

    function formatCurrencyInput(value) {
        // Remove tudo exceto numeros
        let digits = value.replace(/\D/g, '');

        // Se vazio, retorna vazio
        if (!digits) return '';

        // Converte para centavos e formata
        const numValue = parseInt(digits, 10) / 100;

        return numValue.toLocaleString('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        });
    }

    function parseCurrencyInput(value) {
        if (!value) return 0;
        // Remove R$, pontos de milhar, e troca virgula por ponto
        const cleaned = value.replace(/R\$\s?/g, '').replace(/\./g, '').replace(',', '.');
        const num = parseFloat(cleaned);
        return isNaN(num) ? 0 : num;
    }

    function formatNumber(num) {
        if (num >= 1000) {
            return num.toLocaleString('pt-BR');
        }
        return num.toString();
    }

    // ==========================================
    // API CALLS
    // ==========================================
    async function apiSaveResult(resultData) {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/api/resultado`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(resultData)
            });

            if (!response.ok) {
                throw new Error('Erro ao salvar resultado');
            }

            return await response.json();
        } catch (error) {
            console.error('Erro na API:', error);
            return null;
        }
    }

    async function apiSaveUser(userData) {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/api/usuario`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            if (!response.ok) {
                throw new Error('Erro ao salvar usuario');
            }

            return await response.json();
        } catch (error) {
            console.error('Erro na API:', error);
            return null;
        }
    }

    async function apiGetHistory(params) {
        try {
            const query = new URLSearchParams(params).toString();
            const response = await fetch(`${CONFIG.API_BASE}/api/historico?${query}`);

            if (!response.ok) {
                throw new Error('Erro ao buscar historico');
            }

            return await response.json();
        } catch (error) {
            console.error('Erro na API:', error);
            return null;
        }
    }

    async function apiGetCounter() {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/api/contador`);
            if (!response.ok) {
                throw new Error('Erro ao buscar contador');
            }
            return await response.json();
        } catch (error) {
            console.error('Erro na API contador:', error);
            return null;
        }
    }

    // ==========================================
    // UI HELPERS
    // ==========================================
    function showLoading(text = 'Calculando...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        if (loadingText) loadingText.textContent = text;
        if (overlay) overlay.style.display = 'flex';
    }

    function hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) overlay.style.display = 'none';
    }

    function showPopup(popupId) {
        const popup = document.getElementById(popupId);
        if (popup) popup.style.display = 'flex';
    }

    function hidePopup(popupId) {
        const popup = document.getElementById(popupId);
        if (popup) popup.style.display = 'none';
    }

    function getInputValue(id, defaultValue = 0) {
        const el = document.getElementById(id);
        if (!el) return defaultValue;
        const val = parseFloat(el.value);
        return isNaN(val) ? defaultValue : val;
    }

    // ==========================================
    // CALCULATION LOGIC
    // ==========================================
    function calculateKmPercorrido() {
        const kmInicial = getInputValue('kmInicial', 0);
        const kmFinal = getInputValue('kmFinal', 0);
        const kmPercorridoInput = document.getElementById('kmPercorrido');

        // So atualiza se o kmPercorrido estiver vazio ou se foi preenchido automaticamente
        if (kmFinal > 0 && kmInicial >= 0) {
            const kmCalc = kmFinal - kmInicial;
            if (kmCalc > 0 && kmPercorridoInput) {
                kmPercorridoInput.value = kmCalc.toFixed(1);
            }
        }
    }

    function calculateReembolso() {
        const km = getInputValue('kmPercorrido', 0);
        const precoComb = getInputValue('precoCombustivel', 6.29);
        const consumo = getInputValue('consumoMedio', 12);
        const tipoVeiculo = document.getElementById('tipoVeiculo')?.value || 'carro_popular';

        // Busca custos da categoria do veículo
        const vehicleCosts = VEHICLE_COSTS[tipoVeiculo] || VEHICLE_COSTS.carro_popular;

        // Despesas extras usam formato de moeda
        const pedagio = parseCurrencyInput(document.getElementById('valorPedagio')?.value || '');
        const estacionamento = parseCurrencyInput(document.getElementById('valorEstacionamento')?.value || '');
        const alimentacao = parseCurrencyInput(document.getElementById('valorAlimentacao')?.value || '');
        const outras = parseCurrencyInput(document.getElementById('valorOutras')?.value || '');

        // Calculos de custos por km usando taxas da categoria
        const combustivel = consumo > 0 ? (km / consumo) * precoComb : 0;
        const depreciacao = km * vehicleCosts.depreciacao;
        const seguro = km * vehicleCosts.seguro;
        const custosFixos = km * vehicleCosts.custos_fixos;  // Combo: Manutenção + Pneus + IPVA

        // Custo total por km (combustível + custos fixos da categoria)
        const custoPorKm = combustivel + depreciacao + seguro + custosFixos;
        const valorPorKm = km > 0 ? custoPorKm / km : 0;

        // Despesas extras (fixas)
        const despesasExtras = pedagio + estacionamento + alimentacao + outras;

        // Total = custos por km + despesas extras
        const total = custoPorKm + despesasExtras;

        return {
            km,
            precoCombustivel: precoComb,
            consumoMedio: consumo,
            combustivel,
            pedagio,
            estacionamento,
            alimentacao,
            outras,
            depreciacao,
            seguro,
            custosFixos,          // Combo: Manutenção + Pneus + IPVA
            custoPorKm,
            despesasExtras,
            total,
            valorPorKm,
            tipoVeiculo,
            vehicleCosts,         // Taxas usadas no cálculo
            placaVeiculo: document.getElementById('placaVeiculo')?.value || null,
            modeloVeiculo: document.getElementById('modeloVeiculo')?.value || null,
            dataViagem: document.getElementById('dataViagem')?.value || new Date().toISOString().split('T')[0],
            tipoRegistro: document.getElementById('tipoRegistro')?.value || 'individual',
            descricao: document.getElementById('descricaoViagem')?.value || null
        };
    }

    // Historico do dia (armazenado localmente)
    function getDayHistory() {
        const data = getStorageData();
        const hoje = new Date().toISOString().split('T')[0];

        if (!data.historiaDia || data.historiaDia.data !== hoje) {
            data.historiaDia = { data: hoje, viagens: [] };
            saveStorageData(data);
        }
        return data.historiaDia.viagens;
    }

    function addToDayHistory(result) {
        const data = getStorageData();
        const hoje = new Date().toISOString().split('T')[0];

        if (!data.historiaDia || data.historiaDia.data !== hoje) {
            data.historiaDia = { data: hoje, viagens: [] };
        }

        data.historiaDia.viagens.push({
            id: Date.now(),
            km: result.km,
            total: result.total,
            hora: new Date().toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }),
            placa: result.placaVeiculo,
            tipo: result.tipoRegistro,
            descricao: result.descricao
        });

        saveStorageData(data);
        updateDayHistoryDisplay();
    }

    function updateDayHistoryDisplay() {
        const viagens = getDayHistory();
        const card = document.getElementById('cardHistoricoDia');
        const lista = document.getElementById('listaHistoricoDia');
        const totalDisplay = document.getElementById('totalDiaDisplay');

        if (viagens.length === 0) {
            if (card) card.style.display = 'none';
            return;
        }

        if (card) card.style.display = 'block';

        const totalDia = viagens.reduce((acc, v) => acc + v.total, 0);
        const totalKm = viagens.reduce((acc, v) => acc + v.km, 0);

        if (totalDisplay) {
            totalDisplay.textContent = formatMoney(totalDia);
        }

        if (lista) {
            lista.innerHTML = '';
            viagens.forEach(v => {
                const item = document.createElement('div');
                item.className = 'historico-dia-item';

                const info = document.createElement('div');
                info.className = 'historico-dia-info';

                const kmSpan = document.createElement('span');
                kmSpan.className = 'historico-dia-km';
                kmSpan.textContent = `${v.km.toFixed(1)} km`;
                info.appendChild(kmSpan);

                if (v.placa) {
                    info.appendChild(document.createTextNode(` • ${v.placa}`));
                }
                if (v.descricao) {
                    const em = document.createElement('em');
                    em.textContent = ` • ${v.descricao}`;
                    info.appendChild(em);
                }

                const horaSpan = document.createElement('span');
                horaSpan.style.opacity = '0.6';
                horaSpan.textContent = ` • ${v.hora}`;
                info.appendChild(horaSpan);

                const valor = document.createElement('div');
                valor.className = 'historico-dia-valor';
                valor.textContent = formatMoney(v.total);

                item.appendChild(info);
                item.appendChild(valor);
                lista.appendChild(item);
            });
        }
    }

    function displayResult(result) {
        // Esconde estado vazio, mostra resultado
        const emptyResult = document.getElementById('emptyResult');
        const resultadoCalculo = document.getElementById('resultadoCalculo');

        if (emptyResult) emptyResult.style.display = 'none';
        if (resultadoCalculo) resultadoCalculo.style.display = 'block';

        // Atualiza valores principais
        setText('valorTotalReembolso', formatMoney(result.total));
        setText('kmTotalDisplay', `${result.km.toFixed(1)} km`);
        setText('valorPorKmDisplay', `${formatMoney(result.valorPorKm)}/km`);

        // Custos por km - valores já calculados
        setText('detCombustivel', formatMoney(result.combustivel));
        setText('detDepreciacao', formatMoney(result.depreciacao));
        setText('detSeguro', formatMoney(result.seguro));
        setText('detCustosFixos', formatMoney(result.custosFixos));

        // Despesas extras - mostra apenas se tiver valor
        const despesasSection = document.getElementById('despesasExtrasSection');
        const hasDespesas = result.despesasExtras > 0;

        if (despesasSection) {
            despesasSection.style.display = hasDespesas ? 'block' : 'none';
        }

        // Mostra/esconde cada item de despesa
        showDespesaItem('itemPedagio', 'detPedagio', result.pedagio);
        showDespesaItem('itemEstacionamento', 'detEstacionamento', result.estacionamento);
        showDespesaItem('itemAlimentacao', 'detAlimentacao', result.alimentacao);
        showDespesaItem('itemOutras', 'detOutras', result.outras);
    }

    function showDespesaItem(itemId, valueId, value) {
        const item = document.getElementById(itemId);
        if (item) {
            item.style.display = value > 0 ? 'block' : 'none';
        }
        setText(valueId, formatMoney(value));
    }

    function setText(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    function resetForm() {
        const form = document.getElementById('formCalculo');
        if (form) form.reset();

        // Reset valores padrao (usando default do carro_popular)
        setValue('precoCombustivel', '6.29');
        setValue('consumoMedio', VEHICLE_COSTS.carro_popular.consumo_default.toFixed(1));
        setValue('valorPedagio', '0');
        setValue('valorEstacionamento', '0');
        setValue('valorAlimentacao', '0');
        setValue('valorOutras', '0');

        // Esconde resultado
        const emptyResult = document.getElementById('emptyResult');
        const resultadoCalculo = document.getElementById('resultadoCalculo');

        if (emptyResult) emptyResult.style.display = 'block';
        if (resultadoCalculo) resultadoCalculo.style.display = 'none';
    }

    function setValue(id, value) {
        const el = document.getElementById(id);
        if (el) el.value = value;
    }

    // ==========================================
    // MAIN FLOW
    // ==========================================
    let lastResult = null;
    let savedResultId = null;

    async function handleCalculate(e) {
        e.preventDefault();

        const km = getInputValue('kmPercorrido', 0);
        if (km <= 0) {
            alert('Informe o KM percorrido para calcular.');
            document.getElementById('kmPercorrido')?.focus();
            return;
        }

        // Calcula
        lastResult = calculateReembolso();

        // Mostra loading
        showLoading('Calculando...');

        // Salva resultado via API (em background)
        const cookieId = getCookieId();
        const savePromise = apiSaveResult({
            cookie_id: cookieId,
            km_percorrido: lastResult.km,
            preco_combustivel: lastResult.precoCombustivel,
            consumo_medio: lastResult.consumoMedio,
            valor_reembolso: lastResult.total,
            tipo_veiculo: lastResult.tipoVeiculo,
            dados_completos: lastResult
        });

        // Aguarda pelo menos 500ms pra animacao ficar legal
        await Promise.all([
            savePromise.then(res => { savedResultId = res?.id; }),
            new Promise(resolve => setTimeout(resolve, 500))
        ]);

        hideLoading();

        // Exibe resultado
        displayResult(lastResult);

        // Scroll suave para o resultado
        setTimeout(() => {
            const cardResultado = document.getElementById('cardResultado');
            if (cardResultado) {
                cardResultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        }, 100);

        // Adiciona ao historico do dia
        addToDayHistory(lastResult);

        // Se nao tem telefone salvo, mostra popup de captura
        if (!getUserPhone()) {
            setTimeout(() => {
                showPopup('popupCaptura');
            }, 300);
        }
    }

    async function handleSaveUserData() {
        const nomeInput = document.getElementById('inputNome');
        const whatsappInput = document.getElementById('inputWhatsapp');
        const empresaInput = document.getElementById('inputEmpresa');

        const nome = nomeInput?.value?.trim() || '';
        const telefone = cleanPhone(whatsappInput?.value || '');
        const nomeEmpresa = empresaInput?.value?.trim() || null;

        if (!nome) {
            alert('Informe seu nome.');
            nomeInput?.focus();
            return;
        }

        if (telefone.length < 10) {
            alert('Informe um WhatsApp valido.');
            whatsappInput?.focus();
            return;
        }

        showLoading('Salvando...');

        const cookieId = getCookieId();
        await apiSaveUser({
            nome,
            telefone,
            nome_empresa: nomeEmpresa,
            cookie_id: cookieId
        });

        // Salva telefone local
        setUserPhone(telefone);

        hideLoading();
        hidePopup('popupCaptura');
    }

    function handleSkipCapture() {
        hidePopup('popupCaptura');
    }

    async function handleSearchHistory() {
        const input = document.getElementById('inputBuscarWhatsapp');
        const telefone = cleanPhone(input?.value || '');

        if (telefone.length < 10) {
            alert('Informe um WhatsApp valido.');
            input?.focus();
            return;
        }

        showLoading('Buscando...');

        const data = await apiGetHistory({ telefone });

        hideLoading();

        const resultadoDiv = document.getElementById('historicoResultado');
        const vazioDiv = document.getElementById('historicoVazio');
        const listaDiv = document.getElementById('listaHistorico');

        if (data?.resultados && data.resultados.length > 0) {
            if (vazioDiv) vazioDiv.style.display = 'none';
            if (resultadoDiv) resultadoDiv.style.display = 'block';

            // Renderiza lista com DOM seguro (usando createHistoricoItem)
            if (listaDiv) {
                listaDiv.innerHTML = '';
                data.resultados.slice(0, 10).forEach(r => {
                    const item = createHistoricoItem(r);
                    listaDiv.appendChild(item);
                });
            }

            // Atualiza cookie_id e telefone local
            if (data.usuario) {
                const storageData = getStorageData();
                storageData.cookie_id = data.usuario.cookie_id;
                storageData.telefone = telefone;
                saveStorageData(storageData);
            }
        } else {
            if (resultadoDiv) resultadoDiv.style.display = 'none';
            if (vazioDiv) vazioDiv.style.display = 'block';
        }
    }

    function handleNewCalculation() {
        resetForm();
        // Switch to resultado tab
        switchTab('resultado');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // ==========================================
    // HISTÓRICO - ITEM RENDERING
    // ==========================================
    function createHistoricoItem(r) {
        const date = new Date(r.created_at);
        const dateStr = date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Dados extras do JSON
        const dados = r.dados_completos || {};
        const placa = dados.placaVeiculo || null;
        const descricao = dados.descricao || null;
        const tipoVeiculo = formatTipoVeiculo(r.tipo_veiculo);

        const item = document.createElement('div');
        item.className = 'historico-item historico-item-clickable';
        item.setAttribute('role', 'button');
        item.setAttribute('tabindex', '0');

        // Header: data e valor
        const header = document.createElement('div');
        header.className = 'historico-item-header';

        const dateSpan = document.createElement('span');
        dateSpan.className = 'historico-item-date';
        dateSpan.textContent = dateStr;

        const valueSpan = document.createElement('span');
        valueSpan.className = 'historico-item-value';
        valueSpan.textContent = formatMoney(r.valor_reembolso);

        header.appendChild(dateSpan);
        header.appendChild(valueSpan);

        // Detalhes: km, tipo, placa
        const details = document.createElement('div');
        details.className = 'historico-item-details';

        let detailsText = `${r.km_percorrido} km • ${tipoVeiculo}`;
        if (placa) {
            detailsText += ` • ${placa}`;
        }
        details.textContent = detailsText;

        // Descrição (se houver)
        if (descricao) {
            const descSpan = document.createElement('div');
            descSpan.className = 'historico-item-descricao';
            descSpan.textContent = descricao;
            item.appendChild(header);
            item.appendChild(details);
            item.appendChild(descSpan);
        } else {
            item.appendChild(header);
            item.appendChild(details);
        }

        // Indicador de clique
        const clickHint = document.createElement('span');
        clickHint.className = 'historico-item-hint';
        clickHint.textContent = 'Ver detalhes →';
        item.appendChild(clickHint);

        // Click handler para abrir detalhes
        item.addEventListener('click', () => showHistoricoDetalhes(r));
        item.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') showHistoricoDetalhes(r);
        });

        return item;
    }

    function formatTipoVeiculo(tipo) {
        const map = {
            'moto': 'Moto',
            'carro_popular': 'Popular',
            'carro_medio': 'Médio',
            'carro_suv': 'SUV/Pickup'
        };
        return map[tipo] || tipo || 'Carro';
    }

    function showHistoricoDetalhes(registro) {
        const dados = registro.dados_completos || {};

        // Criar modal de detalhes
        let modal = document.getElementById('popupDetalhesHistorico');
        if (!modal) {
            modal = createDetalhesModal();
            document.body.appendChild(modal);
        }

        // Preencher dados
        const date = new Date(registro.created_at);
        const dateStr = date.toLocaleDateString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });

        // Valores
        const combustivel = dados.combustivel || 0;
        const depreciacao = dados.depreciacao || 0;
        const seguro = dados.seguro || 0;
        const custosFixos = dados.custosFixos || 0;
        const despesasExtras = dados.despesasExtras || 0;

        document.getElementById('detalheData').textContent = dateStr;
        document.getElementById('detalheKm').textContent = `${registro.km_percorrido} km`;
        document.getElementById('detalheTipo').textContent = formatTipoVeiculo(registro.tipo_veiculo);
        document.getElementById('detalhePlaca').textContent = dados.placaVeiculo || '-';
        document.getElementById('detalheDescricao').textContent = dados.descricao || '-';
        document.getElementById('detalheTotal').textContent = formatMoney(registro.valor_reembolso);
        document.getElementById('detalhePorKm').textContent = `${formatMoney(registro.valor_reembolso / registro.km_percorrido)}/km`;

        // Breakdown
        document.getElementById('detalheCombustivel').textContent = formatMoney(combustivel);
        document.getElementById('detalheDepreciacao').textContent = formatMoney(depreciacao);
        document.getElementById('detalheSeguro').textContent = formatMoney(seguro);
        document.getElementById('detalheCustosFixos').textContent = formatMoney(custosFixos);

        // Despesas extras
        const extrasSection = document.getElementById('detalheExtrasSection');
        if (despesasExtras > 0) {
            extrasSection.style.display = 'block';
            document.getElementById('detalheExtras').textContent = formatMoney(despesasExtras);
        } else {
            extrasSection.style.display = 'none';
        }

        modal.style.display = 'flex';
    }

    function createDetalhesModal() {
        const modal = document.createElement('div');
        modal.id = 'popupDetalhesHistorico';
        modal.className = 'popup-overlay';
        modal.innerHTML = `
            <div class="popup-container popup-detalhes">
                <div class="popup-header">
                    <h3>Detalhes do Cálculo</h3>
                    <button class="popup-close" id="btnFecharDetalhes">&times;</button>
                </div>
                <div class="popup-body">
                    <div class="detalhes-info-grid">
                        <div class="detalhes-info-item">
                            <span class="detalhes-label">Data</span>
                            <span class="detalhes-value" id="detalheData">-</span>
                        </div>
                        <div class="detalhes-info-item">
                            <span class="detalhes-label">Distância</span>
                            <span class="detalhes-value" id="detalheKm">-</span>
                        </div>
                        <div class="detalhes-info-item">
                            <span class="detalhes-label">Veículo</span>
                            <span class="detalhes-value" id="detalheTipo">-</span>
                        </div>
                        <div class="detalhes-info-item">
                            <span class="detalhes-label">Placa</span>
                            <span class="detalhes-value" id="detalhePlaca">-</span>
                        </div>
                    </div>
                    <div class="detalhes-descricao-box">
                        <span class="detalhes-label">Descrição</span>
                        <span class="detalhes-value" id="detalheDescricao">-</span>
                    </div>
                    <div class="detalhes-resultado">
                        <div class="detalhes-total">
                            <span>Valor Total</span>
                            <span id="detalheTotal">R$ 0,00</span>
                        </div>
                        <div class="detalhes-porkm">
                            <span id="detalhePorKm">R$ 0,00/km</span>
                        </div>
                    </div>
                    <div class="detalhes-breakdown">
                        <h4>Composição do Valor</h4>
                        <div class="detalhes-breakdown-grid">
                            <div class="detalhes-breakdown-item">
                                <span>Combustível</span>
                                <span id="detalheCombustivel">R$ 0,00</span>
                            </div>
                            <div class="detalhes-breakdown-item">
                                <span>Depreciação</span>
                                <span id="detalheDepreciacao">R$ 0,00</span>
                            </div>
                            <div class="detalhes-breakdown-item">
                                <span>Seguro</span>
                                <span id="detalheSeguro">R$ 0,00</span>
                            </div>
                            <div class="detalhes-breakdown-item">
                                <span>Outros custos</span>
                                <span id="detalheCustosFixos">R$ 0,00</span>
                            </div>
                        </div>
                        <div class="detalhes-breakdown-item" id="detalheExtrasSection" style="display:none; margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--cor-borda);">
                            <span>Despesas extras</span>
                            <span id="detalheExtras">R$ 0,00</span>
                        </div>
                    </div>
                </div>
                <div class="popup-footer">
                    <button class="btn btn-primary" id="btnOkDetalhes">Fechar</button>
                </div>
            </div>
        `;

        // Event listeners
        modal.querySelector('#btnFecharDetalhes').addEventListener('click', () => modal.style.display = 'none');
        modal.querySelector('#btnOkDetalhes').addEventListener('click', () => modal.style.display = 'none');
        modal.addEventListener('click', (e) => {
            if (e.target === modal) modal.style.display = 'none';
        });

        return modal;
    }

    // ==========================================
    // TABS FUNCTIONALITY
    // ==========================================
    function initTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const tabName = btn.dataset.tab;
                switchTab(tabName);
            });
        });
    }

    function switchTab(tabName) {
        // Update buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.dataset.tabContent === tabName);
        });
    }

    async function handleSearchHistoryInline() {
        const input = document.getElementById('inputHistoricoInline');
        const telefone = cleanPhone(input?.value || '');

        if (telefone.length < 10) {
            alert('Informe um WhatsApp válido.');
            input?.focus();
            return;
        }

        showLoading('Buscando histórico...');

        const data = await apiGetHistory({ telefone });

        hideLoading();

        const resultadoDiv = document.getElementById('historicoInlineResultado');
        const vazioDiv = document.getElementById('historicoInlineVazio');
        const listaDiv = document.getElementById('listaHistoricoInline');

        if (data?.resultados && data.resultados.length > 0) {
            if (vazioDiv) vazioDiv.style.display = 'none';
            if (resultadoDiv) resultadoDiv.style.display = 'block';

            // Render list with safe text content
            if (listaDiv) {
                listaDiv.innerHTML = '';
                data.resultados.slice(0, 10).forEach(r => {
                    const item = createHistoricoItem(r);
                    listaDiv.appendChild(item);
                });
            }

            // Update local cookie_id and phone
            if (data.usuario) {
                const storageData = getStorageData();
                storageData.cookie_id = data.usuario.cookie_id;
                storageData.telefone = telefone;
                saveStorageData(storageData);
            }

            // Scroll to the card
            setTimeout(() => {
                const cardResultado = document.getElementById('cardResultado');
                if (cardResultado) {
                    cardResultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        } else {
            if (resultadoDiv) resultadoDiv.style.display = 'none';
            if (vazioDiv) {
                vazioDiv.style.display = 'block';
                vazioDiv.querySelector('p').textContent = 'Nenhum histórico encontrado para este número.';
            }
        }
    }

    function handleShare() {
        if (!lastResult) return;

        // Formata data
        const dataViagem = lastResult.dataViagem
            ? new Date(lastResult.dataViagem + 'T12:00:00').toLocaleDateString('pt-BR')
            : new Date().toLocaleDateString('pt-BR');

        // Formata tipo veículo
        const tipoDisplay = formatTipoVeiculo(lastResult.tipoVeiculo);

        // Monta texto com detalhes
        let text = `📊 Calculei meu reembolso KM:\n\n`;
        text += `📅 Data: ${dataViagem}\n`;
        text += `🚗 Veículo: ${tipoDisplay}`;
        if (lastResult.placaVeiculo) {
            text += ` (${lastResult.placaVeiculo})`;
        }
        text += `\n`;
        text += `📏 Distância: ${lastResult.km.toFixed(1)} km\n`;
        text += `\n`;
        text += `💰 Total: ${formatMoney(lastResult.total)}\n`;
        text += `📈 Por km: ${formatMoney(lastResult.valorPorKm)}\n`;
        if (lastResult.descricao) {
            text += `\n📝 ${lastResult.descricao}\n`;
        }
        text += `\n🔗 Calcule o seu: ${window.location.href}`;

        if (navigator.share) {
            navigator.share({
                title: 'Calculadora de Reembolso KM',
                text: text,
                url: window.location.href
            }).catch(() => {});
        } else {
            // Fallback: copia pro clipboard
            navigator.clipboard.writeText(text).then(() => {
                showToast('Resultado copiado para a área de transferência!');
            }).catch(() => {
                // Fallback do fallback: mostra em alert
                prompt('Copie o texto abaixo:', text);
            });
        }
    }

    // Toast notification
    function showToast(message, duration = 3000) {
        let toast = document.getElementById('toastNotification');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toastNotification';
            toast.className = 'toast-notification';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), duration);
    }

    // ==========================================
    // EVENT LISTENERS
    // ==========================================
    function init() {
        // Formulario principal
        const form = document.getElementById('formCalculo');
        if (form) {
            form.addEventListener('submit', handleCalculate);
        }

        // Calcula KM percorrido automaticamente
        const kmInicial = document.getElementById('kmInicial');
        const kmFinal = document.getElementById('kmFinal');
        if (kmInicial) kmInicial.addEventListener('input', calculateKmPercorrido);
        if (kmFinal) kmFinal.addEventListener('input', calculateKmPercorrido);

        // Botao novo calculo
        const btnNovo = document.getElementById('btnNovoCalculo');
        if (btnNovo) btnNovo.addEventListener('click', handleNewCalculation);

        // Botao compartilhar
        const btnCompartilhar = document.getElementById('btnCompartilhar');
        if (btnCompartilhar) btnCompartilhar.addEventListener('click', handleShare);

        // Popup captura
        const btnFecharPopup = document.getElementById('btnFecharPopup');
        const btnPular = document.getElementById('btnPular');
        const btnSalvar = document.getElementById('btnSalvarDados');

        if (btnFecharPopup) btnFecharPopup.addEventListener('click', () => hidePopup('popupCaptura'));
        if (btnPular) btnPular.addEventListener('click', handleSkipCapture);
        if (btnSalvar) btnSalvar.addEventListener('click', handleSaveUserData);

        // Formata WhatsApp ao digitar
        const inputWhatsapp = document.getElementById('inputWhatsapp');
        if (inputWhatsapp) {
            inputWhatsapp.addEventListener('input', (e) => {
                e.target.value = formatPhone(e.target.value);
            });
        }

        // Popup historico
        const btnHistorico = document.getElementById('btnHistorico');
        const btnFecharHistorico = document.getElementById('btnFecharHistorico');
        const btnCancelarHistorico = document.getElementById('btnCancelarHistorico');
        const btnBuscarHistorico = document.getElementById('btnBuscarHistorico');

        if (btnHistorico) btnHistorico.addEventListener('click', () => {
            // Switch to history tab and scroll to result card
            switchTab('historico');

            // Preenche telefone se já tiver
            const savedPhone = getUserPhone();
            const inputInline = document.getElementById('inputHistoricoInline');
            if (savedPhone && inputInline) {
                inputInline.value = formatPhone(savedPhone);
            }

            // Scroll to result card
            setTimeout(() => {
                const cardResultado = document.getElementById('cardResultado');
                if (cardResultado) {
                    cardResultado.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 100);
        });

        if (btnFecharHistorico) btnFecharHistorico.addEventListener('click', () => hidePopup('popupHistorico'));
        if (btnCancelarHistorico) btnCancelarHistorico.addEventListener('click', () => hidePopup('popupHistorico'));
        if (btnBuscarHistorico) btnBuscarHistorico.addEventListener('click', handleSearchHistory);

        // Formata WhatsApp historico ao digitar
        const inputBuscarWhatsapp = document.getElementById('inputBuscarWhatsapp');
        if (inputBuscarWhatsapp) {
            inputBuscarWhatsapp.addEventListener('input', (e) => {
                e.target.value = formatPhone(e.target.value);
            });

            // Enter para buscar
            inputBuscarWhatsapp.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSearchHistory();
                }
            });
        }

        // Tabs na seção de resultado
        initTabs();

        // Inline history search
        const btnBuscarInline = document.getElementById('btnBuscarInline');
        if (btnBuscarInline) {
            btnBuscarInline.addEventListener('click', handleSearchHistoryInline);
        }

        const inputHistoricoInline = document.getElementById('inputHistoricoInline');
        if (inputHistoricoInline) {
            inputHistoricoInline.addEventListener('input', (e) => {
                e.target.value = formatPhone(e.target.value);
            });
            inputHistoricoInline.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    handleSearchHistoryInline();
                }
            });

            // Preenche com telefone salvo
            const savedPhone = getUserPhone();
            if (savedPhone) {
                inputHistoricoInline.value = formatPhone(savedPhone);
            }
        }

        // Fecha popup ao clicar fora
        document.querySelectorAll('.popup-overlay').forEach(popup => {
            popup.addEventListener('click', (e) => {
                if (e.target === popup) {
                    popup.style.display = 'none';
                }
            });
        });

        // Ajusta consumo baseado no tipo de veiculo (usando VEHICLE_COSTS)
        const tipoVeiculoSelect = document.getElementById('tipoVeiculo');
        if (tipoVeiculoSelect) {
            tipoVeiculoSelect.addEventListener('change', (e) => {
                const vehicleCosts = VEHICLE_COSTS[e.target.value] || VEHICLE_COSTS.carro_popular;
                setValue('consumoMedio', vehicleCosts.consumo_default.toFixed(1));
            });
        }

        // Mascaras de moeda nos inputs de despesas
        const currencyInputs = document.querySelectorAll('.input-currency');
        currencyInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                e.target.value = formatCurrencyInput(e.target.value);
            });
        });

        // Carrega contador
        loadCounter();

        // Configura link CTA com UTMs dinamicos
        setupCTALink();

        // Define data padrao como hoje
        setDefaultDate();

        // Formata placa do veiculo
        const placaInput = document.getElementById('placaVeiculo');
        if (placaInput) {
            placaInput.addEventListener('input', (e) => {
                e.target.value = formatPlaca(e.target.value);
            });
        }

        // Modal de Metodologia
        const linkMetodologia = document.getElementById('linkMetodologia');
        const btnFecharMetodologia = document.getElementById('btnFecharMetodologia');
        const btnEntendidoMetodologia = document.getElementById('btnEntendidoMetodologia');

        if (linkMetodologia) {
            linkMetodologia.addEventListener('click', (e) => {
                e.preventDefault();
                showPopup('popupMetodologia');
            });
        }

        if (btnFecharMetodologia) {
            btnFecharMetodologia.addEventListener('click', () => hidePopup('popupMetodologia'));
        }

        if (btnEntendidoMetodologia) {
            btnEntendidoMetodologia.addEventListener('click', () => hidePopup('popupMetodologia'));
        }

        console.log('Calculadora Reembolso KM - Inicializada');
        console.log('Cookie ID:', getCookieId());
    }

    function setDefaultDate() {
        const dataInput = document.getElementById('dataViagem');
        if (dataInput) {
            const hoje = new Date().toISOString().split('T')[0];
            dataInput.value = hoje;
        }
    }

    function formatPlaca(value) {
        // Remove caracteres invalidos
        let cleaned = value.toUpperCase().replace(/[^A-Z0-9]/g, '');

        // Limita a 7 caracteres
        cleaned = cleaned.slice(0, 7);

        // Formata ABC-1234 ou ABC1D23 (Mercosul)
        if (cleaned.length > 3) {
            return cleaned.slice(0, 3) + '-' + cleaned.slice(3);
        }
        return cleaned;
    }

    function setupCTALink() {
        const ctaButton = document.getElementById('btnCTATeams');
        if (!ctaButton) return;

        const baseUrl = 'https://conteleteams.com.br/';

        // Pega UTMs da URL atual
        const currentParams = new URLSearchParams(window.location.search);
        const utmParams = new URLSearchParams();

        // Preserva UTMs existentes
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content'].forEach(param => {
            if (currentParams.has(param)) {
                utmParams.set(param, currentParams.get(param));
            }
        });

        // Define defaults se não tiver UTMs
        if (!utmParams.has('utm_source')) {
            utmParams.set('utm_source', 'calculadora');
        }
        if (!utmParams.has('utm_medium')) {
            utmParams.set('utm_medium', 'ferramenta');
        }
        if (!utmParams.has('utm_campaign')) {
            utmParams.set('utm_campaign', 'calculadora-reembolso-2026-teams');
        }

        // Monta URL final
        const finalUrl = baseUrl + '?' + utmParams.toString();
        ctaButton.href = finalUrl;
    }

    async function loadCounter() {
        const counterDisplay = document.getElementById('counterDisplay');
        if (!counterDisplay) return;

        try {
            const data = await apiGetCounter();
            if (data && data.total !== undefined) {
                // Adiciona base de 300 para parecer que ja tem uso
                const displayTotal = Math.max(data.total + 300, 300);
                counterDisplay.textContent = formatNumber(displayTotal);
            } else {
                counterDisplay.textContent = '300+';
            }
        } catch (e) {
            counterDisplay.textContent = '300+';
        }
    }

    // Inicializa quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
