// Função principal acionada automaticamente por gatilhos
function onChange(e) {
    Logger.clear(); // Limpa os logs anteriores
    Logger.log("onChange foi acionado.");
  
    try {
      var sheet = e.source.getActiveSheet(); // Planilha onde a alteração ocorreu
      Logger.log("Planilha ativa: " + sheet.getName());
  
      // Verifica se a aba é a "Registros de trials"
      if (sheet.getName() !== "Registros de trials") {
        Logger.log("Mudança detectada em uma aba não monitorada. Saindo.");
        return; // Sai da função se não for a aba correta
      }
  
      // Obtém a última linha preenchida
      var lastRow = sheet.getLastRow();
      Logger.log("Última linha preenchida: " + lastRow);
  
      // VERIFICAÇÃO CRÍTICA: Se lastRow for 1 ou menor, não há dados para processar
      if (lastRow <= 1) {
        Logger.log("Não há linhas de dados para processar. Saindo.");
        return;
      }
  
      // Checa o status IMEDIATAMENTE para evitar loops
      var statusCol = sheet.getRange(lastRow, 9).getValue();
      var statusStr = statusCol ? statusCol.toString().trim() : "";
      Logger.log("Status atual da última linha: '" + statusStr + "'");
  
      // Se já tem qualquer status (exceto vazio ou teste-temp-cancelar), não processa
      if (statusStr !== "" && statusStr !== "teste-temp-cancelar") {
        Logger.log("Linha já possui status. Não processando. Status: " + statusStr);
        return;
      }
  
      // LOCK IMEDIATO: Marca como processando para evitar loop
      sheet.getRange(lastRow, 9).setValue("processando...");
      Logger.log("Status marcado como 'processando...' para evitar loop.");
  
      // Pequena pausa para garantir que a mudança seja registrada
      Utilities.sleep(100);
  
      // Verifica se os campos obrigatórios estão preenchidos
      var nome = sheet.getRange(lastRow, 2).getValue();
      var email = sheet.getRange(lastRow, 3).getValue();
      var telefone = sheet.getRange(lastRow, 4).getValue();
      
      Logger.log("Campos - Nome: '" + nome + "', Email: '" + email + "', Telefone: '" + telefone + "'");
      
      if (!nome || !email || !telefone) {
        Logger.log("Campos obrigatórios não preenchidos. Limpando status e saindo.");
        sheet.getRange(lastRow, 9).setValue(""); // Limpa o status para permitir futuro processamento
        return;
      }
  
      // Verifica se o nome contém "teste"
      if (nome && nome.toString().toLowerCase().includes("teste")) {
        Logger.log("Palavra-chave 'teste' encontrada no nome. Cancelando.");
        sheet.getRange(lastRow, 9).setValue("3-temp-can-delete-teste");
        return;
      }
  
      // Verificação de duplicidade simplificada
      var emailLast = email.toString().trim().toLowerCase();
      var phoneLast = formatPhone(telefone.toString().trim());
      
      // Verifica apenas as 3 linhas anteriores
      var duplicado = false;
      var startCheck = Math.max(2, lastRow - 3); // Começa da linha 2 (primeira linha de dados)
      
      for (var i = startCheck; i < lastRow; i++) {
        try {
          var emailCheck = sheet.getRange(i, 3).getValue();
          var phoneCheck = sheet.getRange(i, 4).getValue();
          
          if (emailCheck && phoneCheck) {
            var emailCheckStr = emailCheck.toString().trim().toLowerCase();
            var phoneCheckStr = formatPhone(phoneCheck.toString().trim());
            
            if (emailLast === emailCheckStr && phoneLast === phoneCheckStr) {
              Logger.log("Duplicidade encontrada na linha " + i);
              duplicado = true;
              break;
            }
          }
        } catch (error) {
          Logger.log("Erro ao verificar linha " + i + ": " + error.message);
        }
      }
  
      if (duplicado) {
        sheet.getRange(lastRow, 9).setValue("Duplicado - Email e Telefone");
        return;
      }
  
      // Se chegou até aqui, processa a linha
      processRow(sheet, lastRow);
  
    } catch (error) {
      Logger.log("Erro na função onChange: " + error.message);
      // Em caso de erro, tenta limpar o status para evitar travamento
      try {
        var lastRow = e.source.getActiveSheet().getLastRow();
        if (lastRow > 1) {
          e.source.getActiveSheet().getRange(lastRow, 9).setValue("Erro: " + error.message);
        }
      } catch (cleanupError) {
        Logger.log("Erro ao limpar status: " + cleanupError.message);
      }
    }
  }
  
  /**
   * Formata o número de telefone removendo caracteres não numéricos.
   * Se <= 11 dígitos, adiciona '55' no início.
   * @param {string} telefone - O número de telefone a ser formatado
   * @return {string} - O telefone formatado
   */
  function formatPhone(telefone) {
    if (!telefone) {
      return "";
    }
    
    // Remove todos os caracteres não numéricos
    var numeroLimpo = telefone.toString().replace(/\D/g, '');
    
    // Se o número tiver 11 dígitos ou menos, adiciona '55' no início
    if (numeroLimpo.length <= 11) {
      numeroLimpo = '55' + numeroLimpo;
    }
    
    Logger.log("Telefone original: '" + telefone + "' -> Telefone formatado: '" + numeroLimpo + "'");
    return numeroLimpo;
  }
  
  // Função para processar a linha
  function processRow(sheet, row) {
    Logger.log("Processando a linha: " + row);
  
    var nome = sheet.getRange(row, 2).getValue(); // Nome na coluna B
  
    // Verifica se o nome contém a palavra-chave "teste"
    if (nome && nome.toLowerCase().includes("teste")) {
      Logger.log("Palavra-chave 'teste' encontrada no nome do responsável. Envio cancelado.");
      sheet.getRange(row, 9).setValue("3-temp-can-delete-teste");
      return;
    }
  
    var tamanhoEquipe = sheet.getRange(row, 7).getValue(); // Tamanho da equipe na coluna G
  
    // IDs dos vendedores
    const ID_DANIEL = 13133598;
    const ID_LUANA  = 20997649;
    const ID_SHEILA = 6186902;

    let usuarioId, usuarioNome;

    // Verifica se Daniel está de férias (09/02/2026 a 25/02/2026, retorna dia 26)
    var hoje = new Date();
    var inicioFerias = new Date(2026, 1, 9);  // 09/02/2026 (mês é 0-indexed)
    var fimFerias = new Date(2026, 1, 25, 23, 59, 59); // 25/02/2026 fim do dia
    var danielEmFerias = (hoje >= inicioFerias && hoje <= fimFerias);

    if (danielEmFerias) {
      Logger.log("Daniel em ferias (09/02/2026 a 25/02/2026). Leads redirecionados para Sheila.");
    }

    // Se a equipe for muito grande (>= 21 licenças), direciona para a Sheila
    if (tamanhoEquipe >= 21) {
      usuarioId = ID_SHEILA;
      usuarioNome = "Sheila";

    // Leads com 10 a 20 licenças são distribuídos alternadamente entre Sheila e Daniel
    } else if (tamanhoEquipe >= 10 && tamanhoEquipe <= 20) {
      if (danielEmFerias) {
        // Durante férias do Daniel, todos vão para Sheila
        usuarioId = ID_SHEILA;
        usuarioNome = "Sheila";
        Logger.log("Lead 10-20 licencas redirecionado para Sheila (ferias Daniel).");
      } else {
        // Recupera o contador persistente para distribuição 10-20
        let contadorLeads1020 = PropertiesService.getScriptProperties().getProperty("contadorLeads1020");
        contadorLeads1020 = contadorLeads1020 ? parseInt(contadorLeads1020, 10) : 0;

        // Alterna entre Sheila (par) e Daniel (ímpar)
        if (contadorLeads1020 % 2 === 0) {
          usuarioId = ID_SHEILA;
          usuarioNome = "Sheila";
        } else {
          usuarioId = ID_DANIEL;
          usuarioNome = "Daniel";
        }

        // Incrementa e salva o contador
        contadorLeads1020++;
        PropertiesService.getScriptProperties().setProperty("contadorLeads1020", contadorLeads1020);
        Logger.log("Contador leads 10-20: " + contadorLeads1020 + " | Atribuido para: " + usuarioNome);
      }

    // Leads com 4 a 9 licenças vão para Daniel (ou Sheila se Daniel em férias)
    } else if (tamanhoEquipe >= 4 && tamanhoEquipe <= 9) {
      if (danielEmFerias) {
        usuarioId = ID_SHEILA;
        usuarioNome = "Sheila";
        Logger.log("Lead 4-9 licencas redirecionado para Sheila (ferias Daniel).");
      } else {
        usuarioId = ID_DANIEL;
        usuarioNome = "Daniel";
        Logger.log("Lead 4-9 licencas atribuido para Daniel.");
      }

    // Leads com menos de 4 licenças são considerados inadequados
    } else {
      sheet.getRange(row, 9).setValue("4_lead_inadequado");
      Logger.log("Status atualizado para 4_lead_inadequado.");
      return;
    }
  
    // Envia os dados para o webhook
    sendWebhook(sheet, row, usuarioId, usuarioNome, tamanhoEquipe);
  
    // Atualiza o status para indicar sucesso
    sheet.getRange(row, 9).setValue("0_enviado_para_workflow_n8n");
    Logger.log("Status atualizado para '0_enviado_para_workflow_n8n'.");
  }
  
  // Função para enviar os dados para o webhook
  function sendWebhook(sheet, row, usuarioId, usuarioNome, tamanhoEquipe) {
    Logger.log("Iniciando o envio para o webhook.");
  
    var data = {
      "row_id": row,
      "data_hora": sheet.getRange(row, 1).getValue(), // Coluna A
      "nome": sheet.getRange(row, 2).getValue(), // Coluna B
      "email": sheet.getRange(row, 3).getValue(), // Coluna C
      "telefone": formatPhone(sheet.getRange(row, 4).getValue()), // Coluna D - aplicando formatação
      "empresa": sheet.getRange(row, 5).getValue(), // Coluna E
      "campanha": sheet.getRange(row, 6).getValue(), // Coluna F
      "tamanho_equipe": tamanhoEquipe, // Quantidade de licenças
      "landing_page": sheet.getRange(row, 8).getValue(), // Coluna H
      "info": sheet.getRange(row, 11).getValue(), // Coluna K
      "usuario_id": usuarioId,
      "usuario_nome": usuarioNome
    };
  
    var url = "https://primary-production-2349.up.railway.app/webhook/gera-leads-teams-lp"; // URL do webhook
    var options = {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(data)
    };
  
    try {
      UrlFetchApp.fetch(url, options);
      Logger.log("Dados enviados com sucesso: " + JSON.stringify(data));
    } catch (error) {
      Logger.log("Erro ao enviar dados para o webhook: " + error.message);
    }
  }
  