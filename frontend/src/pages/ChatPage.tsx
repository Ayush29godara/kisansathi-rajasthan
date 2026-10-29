import React, { useState } from 'react';
import { Send, Mic, BookOpen, AlertTriangle, User, Bot } from 'lucide-react';
import { ChatMessage } from '../types';

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      question: "सरसों में सफेद रोली (White Rust) का उपचार क्या है?",
      intent: "disease",
      answer: "सरसों में सफेद रोली की रोकथाम हेतु मैनकोजेब (Mancozeb 75% WP) 2 ग्राम प्रति लीटर पानी की दर से घोल बनाकर छिड़काव करें। पहला लक्षण दिखते ही छिड़काव करना श्रेयस्कर है।",
      sources: [
        {
          doc_title: "रबी फसल पैकेज ऑफ प्रैक्टिसेज",
          source: "कृषि विश्वविद्यालय कोटा / ICAR",
          chunk_text: "सफेद रोली नियंत्रण: मैनकोजेब 75 WP (2 ग्राम/लीटर) का सामयिक छिड़काव करें।",
          relevance_score: 0.89,
        }
      ],
      model_version: "gemini-1.5-flash",
      disclaimer: "सलाह केवल मार्गदर्शन हेतु है। विशिष्ट समस्याओं के लिए निकटतम KVK से संपर्क करें।"
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputQuery.trim()) return;

    const userText = inputQuery;
    setInputQuery('');
    setLoading(true);

    // Scaffold response simulation
    setTimeout(() => {
      const responseMsg: ChatMessage = {
        question: userText,
        intent: "general",
        answer: "राजस्थान कृषि अनुसंधान मैनुअल के अनुसार, संतुलित पोषण (NPK 80:40:40 किग्रा/हेक्टेयर) और सामयिक खरपतवार नियंत्रण से पैदावार में सुधार होता है।",
        sources: [
          {
            doc_title: "राजस्थान फसल प्रबंधन नियमावली",
            source: "ICAR-CAZRI जोधपुर",
            chunk_text: "संतुलित पोषक तत्व प्रबंधन एवं जैविक खाद का प्रयोग मृदा स्वास्थ्य सुधारता है।",
            relevance_score: 0.85,
          }
        ],
        model_version: "gemini-1.5-flash",
        disclaimer: "सलाह केवल मार्गदर्शन हेतु है।"
      };
      setMessages((prev) => [...prev, responseMsg]);
      setLoading(false);
    }, 700);
  };

  return (
    <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-12rem)] bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-slate-800">कृषि सलाहकार चैट (RAG Knowledge Base)</h1>
          <p className="text-xs text-slate-500">प्रमाणित ICAR/CAZRI स्रोतों पर आधारित सुरक्षित सलाह</p>
        </div>
        <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full">
          Gemini 1.5 Flash Grounded
        </span>
      </div>

      {/* Message History */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className="space-y-3">
            {/* User Question */}
            <div className="flex items-start gap-2.5 justify-end">
              <div className="bg-brand-700 text-white rounded-2xl rounded-tr-none px-4 py-2.5 max-w-[85%] text-sm shadow-sm">
                {msg.question}
              </div>
              <div className="w-8 h-8 rounded-full bg-brand-800 text-white flex items-center justify-center flex-shrink-0 text-xs">
                <User className="w-4 h-4" />
              </div>
            </div>

            {/* Advisor Answer */}
            <div className="flex items-start gap-2.5 justify-start">
              <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center flex-shrink-0 text-xs">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-none p-4 max-w-[90%] text-sm space-y-3 shadow-sm">
                <div className="text-slate-800 leading-relaxed">{msg.answer}</div>

                {/* Sources Card */}
                {msg.sources.length > 0 && (
                  <div className="bg-white border border-slate-200 rounded-lg p-3 text-xs">
                    <div className="font-semibold text-slate-700 flex items-center gap-1.5 mb-1.5">
                      <BookOpen className="w-3.5 h-3.5 text-brand-700" />
                      <span>सत्यापित संदर्भ स्रोत (Source Citations):</span>
                    </div>
                    {msg.sources.map((s, sIdx) => (
                      <div key={sIdx} className="text-slate-600 bg-slate-50 p-2 rounded border border-slate-100">
                        <span className="font-medium text-slate-800">{s.doc_title}</span> — {s.source}
                        <p className="mt-1 text-[11px] text-slate-500 italic">"{s.chunk_text}"</p>
                      </div>
                    ))}
                  </div>
                )}

                <div className="text-[10px] text-slate-400 flex items-center gap-1 pt-1 border-t border-slate-200/60">
                  <AlertTriangle className="w-3 h-3 text-amber-500" />
                  <span>{msg.disclaimer}</span>
                </div>
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="text-xs text-slate-400 italic flex items-center gap-2">
            <span className="animate-pulse">कृषि संदर्भ खोजा जा रहा है...</span>
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSend} className="p-3 bg-slate-50 border-t border-slate-200 flex items-center gap-2">
        <button
          type="button"
          onClick={() => setIsRecording(!isRecording)}
          className={`p-2.5 rounded-full transition-colors ${
            isRecording ? 'bg-red-600 text-white animate-pulse' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          }`}
          title="बोलकर सवाल पूछें (Voice input)"
        >
          <Mic className="w-4 h-4" />
        </button>

        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="फसल, बीमारी, खाद या मंडी पर सवाल पूछें..."
          className="flex-1 px-4 py-2 text-sm border border-slate-300 rounded-full focus:ring-2 focus:ring-brand-500 focus:outline-none"
        />

        <button
          type="submit"
          className="p-2.5 bg-brand-700 hover:bg-brand-800 text-white rounded-full transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
