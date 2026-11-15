import React, { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface Props {
  onSubmitText: (text: string) => Promise<void>;
}

export const RequestForm: React.FC<Props> = ({ onSubmitText }) => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || loading) return;
    setLoading(true);
    try {
      await onSubmitText(text.trim());
      setText('');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="panel-card">
      <h3>Incoming Situation Report (Gemini AI)</h3>
      <textarea
        rows={3}
        placeholder="e.g. Urgent: Flooded nursing home at 410 Soquel Ave needs 40 cases of drinking water and 10 insulin kits..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={loading}
      />
      <button type="submit" disabled={loading || !text.trim()} className="btn-primary">
        {loading ? <Loader2 size={16} className="spin" /> : <Send size={16} />}
        {loading ? 'Parsing with Gemini...' : 'Extract & Add Request'}
      </button>
    </form>
  );
};