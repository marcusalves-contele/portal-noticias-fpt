import React, { useState, useEffect } from 'react';
import { ProductType, ReferralFormData } from '../types';
import { submitReferral } from '../services/webhookService';
import { CheckCircle2, AlertCircle, Send, Loader2, DollarSign, Smartphone, User, KeyRound } from 'lucide-react';

const ReferralForm: React.FC = () => {
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

    // Basic Validation
    if (formData.leadPhone.length < 14 || formData.referrerPhone.length < 14) {
      setErrorMessage('Por favor, preencha os telefones corretamente.');
      setStatus('error');
      return;
    }

    try {
      await submitReferral(formData);
      setStatus('success');
    } catch (error) {
      console.error(error);
      setErrorMessage('Ocorreu um erro ao enviar. Tente novamente mais tarde.');
      setStatus('error'); // Switch to 'error' to see the message, or keep it to let them retry
    }
  };

  if (status === 'success') {
    return (
      <div className="bg-white p-8 rounded-2xl shadow-xl h-full min-h-[500px] flex flex-col items-center justify-center text-center animate-fade-in border border-green-100">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
          <CheckCircle2 className="w-10 h-10 text-green-600" />
        </div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Indicação Recebida!</h3>
        <p className="text-gray-600 mb-6">
          Obrigado, {formData.referrerName}. Se o(a) <strong>{formData.leadName}</strong> fechar negócio, você recebe <strong>R$ 300,00</strong> na sua conta!
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
          className="px-6 py-2 bg-contele-blue text-white rounded-lg hover:bg-contele-light transition-colors font-semibold"
        >
          Indicar mais alguém
        </button>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 md:p-8 rounded-2xl shadow-2xl border-t-4 border-contele-accent relative overflow-hidden">
      <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none">
        <DollarSign className="w-32 h-32 text-contele-accent" />
      </div>

      <div className="mb-6 relative z-10">
        <h2 className="text-2xl font-bold text-gray-900">Faça sua indicação</h2>
        <p className="text-sm text-gray-500 mt-1">Preencha os dados abaixo para garantir sua recompensa.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 relative z-10">
        
        {/* Section: Quem você vai indicar? */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-blue-100 text-contele-blue text-xs font-bold px-2 py-1 rounded">1. INDICADO (LEAD)</span>
          </div>
          
          <div className="grid grid-cols-1 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome do Contato</label>
              <div className="relative">
                <User className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  name="leadName"
                  required
                  value={formData.leadName}
                  onChange={handleChange}
                  placeholder="Ex: João Silva"
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-contele-blue focus:border-contele-blue transition-all outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">WhatsApp / Telefone</label>
              <div className="relative">
                <Smartphone className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="tel"
                  name="leadPhone"
                  required
                  value={formData.leadPhone}
                  onChange={(e) => handlePhoneChange(e, 'leadPhone')}
                  placeholder="(11) 99999-9999"
                  className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-contele-blue focus:border-contele-blue transition-all outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Produto de Interesse</label>
              <div className="grid grid-cols-2 gap-3">
                <label className={`cursor-pointer border rounded-lg p-3 flex flex-col items-center justify-center transition-all ${formData.interestedProduct === ProductType.FLEET ? 'bg-blue-50 border-contele-blue text-contele-blue' : 'border-gray-200 hover:border-gray-300'}`}>
                  <input 
                    type="radio" 
                    name="interestedProduct" 
                    value={ProductType.FLEET}
                    checked={formData.interestedProduct === ProductType.FLEET}
                    onChange={() => setFormData(prev => ({...prev, interestedProduct: ProductType.FLEET}))}
                    className="sr-only"
                  />
                  <span className="font-bold text-sm">Fleet</span>
                  <span className="text-[10px] text-gray-500">Gestão de Frotas</span>
                </label>

                <label className={`cursor-pointer border rounded-lg p-3 flex flex-col items-center justify-center transition-all ${formData.interestedProduct === ProductType.TEAMS ? 'bg-blue-50 border-contele-blue text-contele-blue' : 'border-gray-200 hover:border-gray-300'}`}>
                  <input 
                    type="radio" 
                    name="interestedProduct" 
                    value={ProductType.TEAMS}
                    checked={formData.interestedProduct === ProductType.TEAMS}
                    onChange={() => setFormData(prev => ({...prev, interestedProduct: ProductType.TEAMS}))}
                    className="sr-only"
                  />
                  <span className="font-bold text-sm">Teams</span>
                  <span className="text-[10px] text-gray-500">Gestão de Equipes</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-100 my-4"></div>

        {/* Section: Seus Dados */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-green-100 text-green-700 text-xs font-bold px-2 py-1 rounded">2. VOCÊ (QUEM INDICA)</span>
          </div>

          <div className="grid grid-cols-1 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Seu Nome</label>
              <input
                type="text"
                name="referrerName"
                required
                value={formData.referrerName}
                onChange={handleChange}
                placeholder="Seu nome completo"
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-contele-blue focus:border-contele-blue transition-all outline-none"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Seu WhatsApp</label>
                <input
                  type="tel"
                  name="referrerPhone"
                  required
                  value={formData.referrerPhone}
                  onChange={(e) => handlePhoneChange(e, 'referrerPhone')}
                  placeholder="(11) 99999-9999"
                  className="w-full px-4 py-2.5 bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-contele-blue focus:border-contele-blue transition-all outline-none"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1 flex items-center gap-1">
                  Chave PIX <span className="text-green-600 text-xs">(Para receber)</span>
                </label>
                <div className="relative">
                  <KeyRound className="absolute left-3 top-3 w-5 h-5 text-green-600" />
                  <input
                    type="text"
                    name="referrerPixKey"
                    required
                    value={formData.referrerPixKey}
                    onChange={handleChange}
                    placeholder="CPF, Email ou Aleatória"
                    className="w-full pl-10 pr-4 py-2.5 bg-green-50 border border-green-200 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-all outline-none text-gray-800 placeholder-gray-400"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {status === 'error' && (
          <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {errorMessage}
          </div>
        )}

        <button
          type="submit"
          disabled={status === 'loading'}
          className="w-full py-4 bg-contele-accent hover:bg-green-500 text-white font-bold text-lg rounded-xl shadow-lg shadow-green-200 hover:shadow-green-300 transform hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2"
        >
          {status === 'loading' ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              Enviando...
            </>
          ) : (
            <>
              <Send className="w-5 h-5" />
              Indicar e Ganhar R$ 300
            </>
          )}
        </button>
        
        <p className="text-xs text-center text-gray-400 mt-2">
          Seus dados estão seguros. Pagamento realizado após fechamento do contrato.
        </p>
      </form>
    </div>
  );
};

export default ReferralForm;