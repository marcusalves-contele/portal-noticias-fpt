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
        DEPRECIATION_PER_KM: 0.20,
        INSURANCE_PER_KM: 0.15,
        STORAGE_KEY: 'calc_reembolso_km'
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
        const consumo = getInputValue('consumoMedio', 11);

        // Despesas extras usam formato de moeda
        const pedagio = parseCurrencyInput(document.getElementById('valorPedagio')?.value || '');
        const estacionamento = parseCurrencyInput(document.getElementById('valorEstacionamento')?.value || '');
        const alimentacao = parseCurrencyInput(document.getElementById('valorAlimentacao')?.value || '');
        const outras = parseCurrencyInput(document.getElementById('valorOutras')?.value || '');

        // Calculos de custos por km
        const combustivel = consumo > 0 ? (km / consumo) * precoComb : 0;
        const depreciacao = km * CONFIG.DEPRECIATION_PER_KM;
        const seguro = km * CONFIG.INSURANCE_PER_KM;

        // Custo por km (apenas custos variaveis)
        const custoPorKm = combustivel + depreciacao + seguro;
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
            custoPorKm,
            despesasExtras,
            total,
            valorPorKm,
            tipoVeiculo: document.getElementById('tipoVeiculo')?.value || 'carro_popular',
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
            lista.innerHTML = viagens.map(v => `
                <div class="historico-dia-item">
                    <div class="historico-dia-info">
                        <span class="historico-dia-km">${v.km.toFixed(1)} km</span>
                        ${v.placa ? ` • ${v.placa}` : ''}
                        ${v.descricao ? ` • <em>${v.descricao}</em>` : ''}
                        <span style="opacity: 0.6"> • ${v.hora}</span>
                    </div>
                    <div class="historico-dia-valor">${formatMoney(v.total)}</div>
                </div>
            `).join('');
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

        // Custos por km
        setText('detCombustivel', formatMoney(result.combustivel));
        setText('detDepreciacao', formatMoney(result.depreciacao));
        setText('detSeguro', formatMoney(result.seguro));

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

        // Reset valores padrao
        setValue('precoCombustivel', '6.29');
        setValue('consumoMedio', '11.0');
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

            // Renderiza lista
            if (listaDiv) {
                listaDiv.innerHTML = data.resultados.slice(0, 10).map(r => {
                    const date = new Date(r.created_at);
                    const dateStr = date.toLocaleDateString('pt-BR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });

                    return `
                        <div class="historico-item">
                            <div class="historico-item-header">
                                <span class="historico-item-date">${dateStr}</span>
                                <span class="historico-item-value">${formatMoney(r.valor_reembolso)}</span>
                            </div>
                            <div class="historico-item-details">
                                ${r.km_percorrido} km | ${r.tipo_veiculo || 'Carro'}
                            </div>
                        </div>
                    `;
                }).join('');
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
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function handleShare() {
        if (!lastResult) return;

        const text = `Calculei meu reembolso KM:\n\n` +
            `KM: ${lastResult.km.toFixed(1)} km\n` +
            `Total: ${formatMoney(lastResult.total)}\n` +
            `Por km: ${formatMoney(lastResult.valorPorKm)}\n\n` +
            `Calcule o seu: ${window.location.href}`;

        if (navigator.share) {
            navigator.share({
                title: 'Calculadora de Reembolso KM',
                text: text,
                url: window.location.href
            }).catch(() => {});
        } else {
            // Fallback: copia pro clipboard
            navigator.clipboard.writeText(text).then(() => {
                alert('Resultado copiado!');
            }).catch(() => {
                alert('Compartilhe:\n\n' + text);
            });
        }
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
            // Limpa estado anterior
            const resultadoDiv = document.getElementById('historicoResultado');
            const vazioDiv = document.getElementById('historicoVazio');
            if (resultadoDiv) resultadoDiv.style.display = 'none';
            if (vazioDiv) vazioDiv.style.display = 'none';

            // Preenche telefone se ja tiver
            const savedPhone = getUserPhone();
            if (savedPhone) {
                const input = document.getElementById('inputBuscarWhatsapp');
                if (input) input.value = formatPhone(savedPhone);
            }

            showPopup('popupHistorico');
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

        // Fecha popup ao clicar fora
        document.querySelectorAll('.popup-overlay').forEach(popup => {
            popup.addEventListener('click', (e) => {
                if (e.target === popup) {
                    popup.style.display = 'none';
                }
            });
        });

        // Ajusta consumo baseado no tipo de veiculo
        const tipoVeiculo = document.getElementById('tipoVeiculo');
        if (tipoVeiculo) {
            tipoVeiculo.addEventListener('change', (e) => {
                const consumoMap = {
                    'carro_popular': 11.0,
                    'carro_medio': 10.0,
                    'carro_suv': 8.0,
                    'moto': 30.0
                };
                const consumo = consumoMap[e.target.value] || 11.0;
                setValue('consumoMedio', consumo.toFixed(1));
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
