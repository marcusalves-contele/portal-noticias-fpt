import { ReferralFormData, WebhookResponse } from '../types';

// Webhook URL from env var (VITE_ prefix required for Vite to expose to client)
const N8N_WEBHOOK_URL = import.meta.env.VITE_N8N_WEBHOOK_URL ||
  'https://primary-production-2349.up.railway.app/webhook/referral-submission'; 

export const submitReferral = async (data: ReferralFormData): Promise<WebhookResponse> => {
  try {
    // Simulate network delay for better UX
    await new Promise(resolve => setTimeout(resolve, 800));

    const response = await fetch(N8N_WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...data,
        submittedAt: new Date().toISOString(),
        source: 'lp-indique-ganhe-v2'
      }),
    });

    if (!response.ok) {
      // If the webhook endpoint isn't real/reachable during dev, we might throw here.
      // For this demo, if 404/500, we assume it failed.
      // However, for demo purposes without a real backend, we might want to fake success 
      // if the URL is dummy. 
      // UNCOMMENT BELOW TO FORCE SUCCESS IN DEMO MODE IF ENDPOINT IS DOWN:
      // return { success: true, message: 'Enviado com sucesso (Demo)' };
      
      throw new Error(`Erro ao enviar: ${response.statusText}`);
    }

    return {
      success: true,
      message: 'Indicação enviada com sucesso!'
    };
  } catch (error) {
    console.error('Webhook error:', error);
    // return false so the UI can show an error
    throw error;
  }
};