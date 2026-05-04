export interface Receipt {
  id: number;
  filename: string;
  image_path: string;
  ocr_raw_text?: string;
  extracted_date?: string | Date;
  extracted_time?: string;
  sender?: string;
  receiver?: string;
  amount?: number | string; // API can return either number or string
  note?: string;
  confidence_score?: number | string; // API can return either number or string
  status: 'pending' | 'reviewed' | 'confirmed';
  transaction_type?: 'sending' | 'receiving' | 'unknown';
  transaction_confidence?: 'high' | 'medium' | 'low';
  classification_reason?: string;
  detected_template?: string;
  ocr_engine?: string;
  is_salary?: boolean;
  is_manual_income?: boolean;
  income_category?: string;
  created_at: string;
  updated_at: string;
}

export interface ReceiptUpdate {
  extracted_date?: string;
  extracted_time?: string;
  sender?: string;
  receiver?: string;
  amount?: number | string;
  note?: string;
  status?: 'pending' | 'reviewed' | 'confirmed';
  transaction_type?: 'sending' | 'receiving' | 'unknown';
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sourceReceipts?: Receipt[];
}
