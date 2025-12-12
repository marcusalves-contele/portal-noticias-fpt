import { useState, useEffect } from 'react';
import { ProductType, ReferralFormData } from '../types';
import { submitReferral } from '../services/webhookService';
import { CheckCircle2, AlertCircle, Send, Loader2, Smartphone, User, KeyRound } from 'lucide-react';

const ReferralForm = () => {
  const [formData, setFormData] = useState<ReferralFormData>({
    leadName: '',
    leadPhone: '',
    interestedProduct: ProductType.FLEET,
    referrerName: '',
    referrerPhone: '',
    referrerPixKey: '',
  });

  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  // Capture UTM parameters from URL on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const utmUpdates: Partial<ReferralFormData> = {};
    
    const source = params.get('utm_source');
    const medium = params.get('utm_medium');
    const campaign = params.get('utm_campaign');
    const term = params.get('utm_term');
    const content = params.get('utm_content');

    if (source) utmUpdates.utmSource = source;
    if (medium) utmUpdates.utmMedium = medium;
    if (campaign) utmUpdates.utmCampaign = campaign;
    if (term) utmUpdates.utmTerm = term;
    if (content) utmUpdates.utmContent = content;

    if (Object.keys(utmUpdates).length > 0) {
      setFormData(prev => ({ ...prev, ...utmUpdates }));
    }
  }, []);

  // Simple mask for Brazilian phone numbers (XX) XXXXX-XXXX
  const formatPhone = (value: string) => {
    return value
      .replace(/\D/g, '')
      .replace(/^(\d{2})(\d)/g, '($1) $2')
      .replace(/(\d)(\d{4})$/, '$1-$2')
      .slice(0, 15);
  };

  // Validate phone number has 11 digits (DDD + 9 digits)
  const validatePhone = (phone: string): boolean => {
    const digitsOnly = phone.replace(/\D/g, '');
    return digitsOnly.length === 11;
  };

  // Validate PIX key (basic validation)
  const validatePixKey = (pixKey: string): boolean => {
    const trimmed = pixKey.trim();
    if (trimmed.length === 0) return false;

    // CPF: 11 digits
    if (/^\d{11}$/.test(trimmed.replace(/\D/g, ''))) return true;

    // Email
    if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)) return true;

    // Phone: 11 digits
    if (/^\d{11}$/.test(trimmed.replace(/\D/g, ''))) return true;

    // Random key (UUID format or 32+ chars)
    if (trimmed.length >= 32) return true;

    return false;
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>, field: 'leadPhone' | 'referrerPhone') => {
    setFormData(prev => ({ ...prev, [field]: formatPhone(e.target.value) }));
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    setErrorMessage('');

    // Validation
    if (!validatePhone(formData.leadPhone)) {
      setErrorMessage('WhatsApp do contato inválido. Digite um número com DDD (11 dígitos).');
      setStatus('error');
      return;
    }

    if (!validatePhone(formData.referrerPhone)) {
      setErrorMessage('Seu WhatsApp está inválido. Digite um número com DDD (11 dígitos).');
      setStatus('error');
      return;
    }

    if (!validatePixKey(formData.referrerPixKey)) {
      setErrorMessage('Chave PIX inválida. Use CPF (11 dígitos), email, telefone ou chave aleatória.');
      setStatus('error');
      return;
    }

    try {
      // Sanitize data before submission
      const sanitizedData = {
        ...formData,
        leadName: formData.leadName.trim(),
        referrerName: formData.referrerName.trim(),
        referrerPixKey: formData.referrerPixKey.trim(),
      };

      await submitReferral(sanitizedData);
      setStatus('success');
    } catch (error) {
      console.error('[ReferralForm] Submission error:', error);
      const errorMsg = error instanceof Error ? error.message : 'Erro desconhecido';
      setErrorMessage(`Erro ao enviar indicação: ${errorMsg}. Tente novamente ou entre em contato com o suporte.`);
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="bg-white p-6 md:p-8 rounded-2xl shadow-xl h-full min-h-[450px] md:min-h-[500px] flex flex-col items-center justify-center text-center animate-fade-in border border-green-100">
        <div className="w-20 h-20 md:w-24 md:h-24 bg-green-100 rounded-full flex items-center justify-center mb-5 md:mb-6">
          <CheckCircle2 className="w-10 h-10 md:w-12 md:h-12 text-green-600" />
        </div>
        <h3 className="text-xl md:text-2xl lg:text-3xl font-bold text-gray-900 mb-3 px-2">Indicação Recebida!</h3>
        <p className="text-base md:text-lg lg:text-xl text-gray-600 mb-6 md:mb-8 max-w-sm px-4 leading-relaxed">
          Obrigado, <strong>{formData.referrerName}</strong>! Se <strong>{formData.leadName}</strong> fechar negócio, você recebe <strong className="text-green-600">R$ 300,00</strong> no PIX!
        </p>
        <button
          onClick={() => {
            
            // Keep referrer info and UTMs for convenience when referring someone else
            setFormData(prev => ({ 
              ...prev, 
              leadName: '', 
              leadPhone: '' 
            })); 
            setFormData({ ...formData, leadName: '', leadPhone: '' }); // Keep referrer info for convenience
            setStatus('idle');
          }}
          className="px-6 md:px-8 py-3 bg-contele-blue text-white rounded-xl hover:bg-contele-light transition-colors font-bold text-base md:text-lg"
        >
          Indicar mais alguém
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white p-5 md:p-8 rounded-2xl shadow-2xl border-t-4 border-contele-accent relative overflow-hidden">
      <div className="absolute top-3 right-3 md:top-4 md:right-4 opacity-40 pointer-events-none">
        <img
          src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Logo%E2%80%94pix_powered_by_Banco_Central_%28Brazil%2C_2020%29.svg/960px-Logo%E2%80%94pix_powered_by_Banco_Central_%28Brazil%2C_2020%29.svg.png"
          alt=""
          className="w-16 h-16 md:w-24 md:h-24 object-contain"
          aria-hidden="true"
        />
      </div>

      <div className="mb-5 md:mb-6 relative z-10">
        <h2 className="text-xl md:text-2xl lg:text-3xl font-bold text-gray-900">Faça sua indicação</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5 md:space-y-6 relative z-10">

        {/* Section: Quem você vai indicar? */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-blue-100 text-contele-blue text-xs md:text-sm font-bold px-2 md:px-3 py-1.5 rounded">QUEM VOCÊ VAI INDICAR</span>
          </div>
          
          <div className="grid grid-cols-1 gap-4">
            <div>
              <label htmlFor="leadName" className="block text-base font-medium text-gray-700 mb-1">Nome do Contato</label>
              <div className="relative">
                <User className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" aria-hidden="true" />
                <input
                  type="text"
                  id="leadName"
                  name="leadName"
                  required
                  value={formData.leadName}
                  onChange={handleChange}
                  placeholder="Ex: João Silva"
                  aria-label="Nome do contato que você está indicando"
                  className="w-full pl-10 pr-4 py-3 text-base bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-contele-blue focus:border-contele-blue transition-all outline-none"
                />
              </div>
            </div>

            <div>
              <label htmlFor="leadPhone" className="block text-base font-medium text-gray-700 mb-1">WhatsApp</label>
              <div className="relative">
                <Smartphone className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" aria-hidden="true" />
                <input
                  type="tel"
                  id="leadPhone"
                  name="leadPhone"
                  required
                  value={formData.leadPhone}
                  onChange={(e) => handlePhoneChange(e, 'leadPhone')}
                  placeholder="(11) 99999-9999"
                  aria-label="WhatsApp do contato que você está indicando"
                  className="w-full pl-10 pr-4 py-3 text-base bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-contele-blue focus:border-contele-blue transition-all outline-none"
                />
              </div>
            </div>

            <fieldset>
              <legend className="block text-base font-medium text-gray-700 mb-3">Produto de Interesse</legend>
              <div className="grid grid-cols-2 gap-3">
                <label className={`cursor-pointer border-2 rounded-xl p-2.5 md:p-3 flex flex-col items-center justify-center transition-all ${formData.interestedProduct === ProductType.FLEET ? 'bg-blue-50 border-contele-blue text-contele-blue shadow-md' : 'border-gray-200 hover:border-gray-300'}`}>
                  <input
                    type="radio"
                    name="interestedProduct"
                    value={ProductType.FLEET}
                    checked={formData.interestedProduct === ProductType.FLEET}
                    onChange={() => setFormData(prev => ({...prev, interestedProduct: ProductType.FLEET}))}
                    className="sr-only"
                    aria-label="Contele Fleet - Gestão de Frotas"
                  />
                  <span className="font-bold text-base md:text-lg">Fleet</span>
                  <span className="text-xs md:text-sm font-medium text-gray-600 mt-0.5 text-center">Gestão de Frotas</span>
                </label>

                <label className={`cursor-pointer border-2 rounded-xl p-2.5 md:p-3 flex flex-col items-center justify-center transition-all ${formData.interestedProduct === ProductType.TEAMS ? 'bg-blue-50 border-contele-blue text-contele-blue shadow-md' : 'border-gray-200 hover:border-gray-300'}`}>
                  <input
                    type="radio"
                    name="interestedProduct"
                    value={ProductType.TEAMS}
                    checked={formData.interestedProduct === ProductType.TEAMS}
                    onChange={() => setFormData(prev => ({...prev, interestedProduct: ProductType.TEAMS}))}
                    className="sr-only"
                    aria-label="Contele Teams - Gestão de Equipes"
                  />
                  <span className="font-bold text-base md:text-lg">Teams</span>
                  <span className="text-xs md:text-sm font-medium text-gray-600 mt-0.5 text-center">Gestão de Equipes</span>
                </label>
              </div>
            </fieldset>
          </div>
        </div>

        <div className="border-t border-gray-100 my-4"></div>

        {/* Section: Seus Dados */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-green-100 text-green-700 text-xs md:text-sm font-bold px-2 md:px-3 py-1.5 rounded">SEUS DADOS (PARA RECEBER O PIX)</span>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div>
              <label htmlFor="referrerName" className="block text-base font-medium text-gray-700 mb-1">Seu Nome</label>
              <input
                type="text"
                id="referrerName"
                name="referrerName"
                required
                value={formData.referrerName}
                onChange={handleChange}
                placeholder="Seu nome completo"
                aria-label="Seu nome completo para receber o PIX"
                className="w-full px-4 py-3 text-base bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-contele-blue focus:border-contele-blue transition-all outline-none"
              />
            </div>

            <div>
              <label htmlFor="referrerPhone" className="block text-base font-medium text-gray-700 mb-1">Seu WhatsApp</label>
              <input
                type="tel"
                id="referrerPhone"
                name="referrerPhone"
                required
                value={formData.referrerPhone}
                onChange={(e) => handlePhoneChange(e, 'referrerPhone')}
                placeholder="(11) 99999-9999"
                aria-label="Seu WhatsApp para contato"
                className="w-full px-4 py-3 text-base bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-contele-blue focus:border-contele-blue transition-all outline-none"
              />
            </div>

            <div>
              <label htmlFor="referrerPixKey" className="block text-base font-medium text-gray-700 mb-1 flex items-center gap-2 flex-wrap">
                Chave PIX <span className="text-green-600 text-sm font-semibold">(Para receber)</span>
              </label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-3.5 w-5 h-5 text-green-600" aria-hidden="true" />
                <input
                  type="text"
                  id="referrerPixKey"
                  name="referrerPixKey"
                  required
                  value={formData.referrerPixKey}
                  onChange={handleChange}
                  placeholder="CPF, Email ou Aleatória"
                  aria-label="Sua chave PIX para receber o pagamento"
                  aria-describedby="pix-help"
                  className="w-full pl-10 pr-4 py-3 text-base bg-green-50 border border-green-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all outline-none text-gray-800 placeholder-gray-400"
                />
              </div>
              <p id="pix-help" className="text-xs text-gray-500 mt-1">
                Aceita CPF, email, telefone ou chave aleatória
              </p>
            </div>
          </div>
        </div>

        {status === 'error' && (
          <div role="alert" aria-live="assertive" className="p-4 bg-red-50 text-red-600 text-base rounded-lg flex items-center gap-2">
            <AlertCircle className="w-5 h-5" aria-hidden="true" />
            {errorMessage}
          </div>
        )}

        <button
          type="submit"
          disabled={status === 'loading'}
          aria-label={status === 'loading' ? 'Enviando sua indicação, aguarde' : 'Enviar indicação e ganhar R$ 300'}
          className="w-full py-3 md:py-4 bg-contele-accent hover:bg-green-500 text-white font-bold text-lg md:text-xl rounded-xl shadow-lg shadow-green-200 hover:shadow-green-300 transform hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2 md:gap-3 disabled:opacity-70 disabled:cursor-not-allowed disabled:transform-none"
        >
          {status === 'loading' ? (
            <>
              <Loader2 className="w-5 h-5 md:w-6 md:h-6 animate-spin" aria-hidden="true" />
              <span>Enviando...</span>
            </>
          ) : (
            <>
              <Send className="w-5 h-5 md:w-6 md:h-6" aria-hidden="true" />
              <span>Indicar e Ganhar R$ 300</span>
            </>
          )}
        </button>

        <p className="text-sm text-center text-gray-500 mt-3">
          Seus dados estão seguros. Pagamento realizado após fechamento do contrato.
        </p>
      </form>
    </div>
  );
};

export default ReferralForm;