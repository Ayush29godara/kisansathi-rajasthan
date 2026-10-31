import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ThumbsUp, ThumbsDown, Check, Send } from 'lucide-react';
import { submitFeedback } from '../../services/api';

interface FeedbackButtonsProps {
  messageId?: string;
  initialRating?: number | null;
  initialOutcome?: string | null;
  onFeedbackSaved?: (rating: number, outcome?: string) => void;
}

export const FeedbackButtons: React.FC<FeedbackButtonsProps> = ({
  messageId,
  initialRating = null,
  initialOutcome = '',
  onFeedbackSaved,
}) => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const [rating, setRating] = useState<number | null>(initialRating);
  const [outcome, setOutcome] = useState<string>(initialOutcome || '');
  const [showOutcomeInput, setShowOutcomeInput] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [submitted, setSubmitted] = useState<boolean>(initialRating !== null);

  const handleRate = async (selectedRating: number) => {
    setRating(selectedRating);
    setShowOutcomeInput(true);
    setSubmitting(true);
    try {
      await submitFeedback({
        message_id: messageId,
        rating: selectedRating,
        actual_outcome: outcome.trim() || undefined,
      });
      setSubmitted(true);
      if (onFeedbackSaved) {
        onFeedbackSaved(selectedRating, outcome.trim() || undefined);
      }
    } catch (err) {
      console.warn('Feedback submission queued or failed:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveOutcome = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === null) return;
    setSubmitting(true);
    try {
      await submitFeedback({
        message_id: messageId,
        rating,
        actual_outcome: outcome.trim(),
      });
      setSubmitted(true);
      setShowOutcomeInput(false);
      if (onFeedbackSaved) {
        onFeedbackSaved(rating, outcome.trim());
      }
    } catch (err) {
      console.warn('Feedback outcome submission error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-2 pt-2 border-t border-gray-100 flex flex-col space-y-2">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span className="font-medium">
          {isHi ? 'क्या यह सलाह उपयोगी थी?' : 'Was this advice helpful?'}
        </span>
        <div className="flex items-center space-x-1.5" role="group" aria-label="Feedback options">
          <button
            type="button"
            onClick={() => handleRate(1)}
            disabled={submitting}
            aria-label={isHi ? 'उपयोगी सलाह (हाँ)' : 'Helpful advice (Yes)'}
            aria-pressed={rating === 1}
            className={`p-1.5 rounded-md border flex items-center space-x-1 transition focus:outline-none focus:ring-2 focus:ring-green-600 ${
              rating === 1
                ? 'bg-green-100 text-green-800 border-green-300 font-semibold'
                : 'hover:bg-gray-100 text-gray-600 border-gray-200'
            }`}
          >
            <ThumbsUp className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{isHi ? 'हाँ' : 'Yes'}</span>
          </button>

          <button
            type="button"
            onClick={() => handleRate(-1)}
            disabled={submitting}
            aria-label={isHi ? 'अनुपयोगी सलाह (नहीं)' : 'Not helpful advice (No)'}
            aria-pressed={rating === -1}
            className={`p-1.5 rounded-md border flex items-center space-x-1 transition focus:outline-none focus:ring-2 focus:ring-red-600 ${
              rating === -1
                ? 'bg-red-100 text-red-800 border-red-300 font-semibold'
                : 'hover:bg-gray-100 text-gray-600 border-gray-200'
            }`}
          >
            <ThumbsDown className="w-3.5 h-3.5" aria-hidden="true" />
            <span>{isHi ? 'नहीं' : 'No'}</span>
          </button>
        </div>
      </div>

      {showOutcomeInput && (
        <form onSubmit={handleSaveOutcome} className="flex items-center space-x-2 mt-1">
          <input
            type="text"
            value={outcome}
            onChange={(e) => setOutcome(e.target.value)}
            placeholder={
              isHi
                ? 'वास्तविक परिणाम (वैकल्पिक, उदा. 80% फायदा हुआ)'
                : 'Actual outcome (optional, e.g. 80% recovery)'
            }
            aria-label={isHi ? 'वास्तविक परिणाम' : 'Actual outcome'}
            className="flex-1 text-xs border border-gray-300 rounded px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          <button
            type="submit"
            disabled={submitting}
            aria-label={isHi ? 'परिणाम सहेजें' : 'Save outcome'}
            className="bg-primary-600 text-white p-1.5 rounded hover:bg-primary-700 transition focus:outline-none focus:ring-2 focus:ring-primary-600"
          >
            <Send className="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </form>
      )}

      {submitted && !showOutcomeInput && (
        <div className="flex items-center space-x-1 text-[11px] text-green-700 font-medium">
          <Check className="w-3.5 h-3.5" aria-hidden="true" />
          <span>
            {isHi ? 'आपकी प्रतिक्रिया दर्ज कर ली गई है।' : 'Feedback recorded. Thank you!'}
            {outcome && ` (${outcome})`}
          </span>
        </div>
      )}
    </div>
  );
};
