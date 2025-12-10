export enum ProductType {
  FLEET = 'Contele Fleet',
  TEAMS = 'Contele Teams'
}

export interface ReferralFormData {
  // Lead (Indicado)
  leadName: string;
  leadPhone: string;
  interestedProduct: ProductType;

  // Referrer (Quem Indica)
  referrerName: string;
  referrerPhone: string;
  referrerPixKey: string;
}

export interface WebhookResponse {
  success: boolean;
  message: string;
}
