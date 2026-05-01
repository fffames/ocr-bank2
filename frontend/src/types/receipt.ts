export interface Receipt {
  id: number;
  filename: string;
  image_path: string;
  ocr_raw_text?: string;
  extracted_date?: string;
  extracted_time?: string;
  sender?: string;
  receiver?: string;
  amount?: number;
  note?: string;
  confidence_score?: number;
  status: 'pending' | 'reviewed' | 'confirmed';
  created_at: string;
  updated_at: string;
}

export interface ReceiptUpdate {
  extracted_date?: string;
  extracted_time?: string;
  sender?: string;
  receiver?: string;
  amount?: number;
  note?: string;
  status?: 'pending' | 'reviewed' | 'confirmed';
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sourceReceipts?: Receipt[];
}
