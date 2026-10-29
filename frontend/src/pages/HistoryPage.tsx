import React from 'react';
import { History, MessageSquare, Stethoscope, Clock } from 'lucide-react';

export const HistoryPage: React.FC = () => {
  const historyItems = [
    {
      id: '1',
      type: 'chat',
      title: 'सरसों में सफेद रोली (White Rust) का उपचार',
      date: '2026-10-28',
      summary: 'मैनकोजेब 75% WP 2 ग्राम/लीटर का छिड़काव अनुशंसित।',
      source: 'कृषि विश्वविद्यालय कोटा',
    },
    {
      id: '2',
      type: 'diagnose',
      title: 'पत्ती रोग फोटो विश्लेषण',
      date: '2026-10-25',
      summary: 'White Rust पहचाना गया (विश्वास 82%)।',
      source: 'इन-ब्राउज़र ONNX',
    },
  ];

  return (
    <div className="max-w-3xl mx-auto my-6 space-y-6">
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-700 flex items-center justify-center">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">परामर्श इतिहास (Advisory History)</h1>
            <p className="text-xs text-slate-500">आपके द्वारा पूछे गए पिछले प्रश्न और रोग जांच रिकॉर्ड</p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {historyItems.map((item) => (
          <div key={item.id} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-start gap-3">
            <div className="p-2 rounded-lg bg-slate-100 text-slate-700 flex-shrink-0 mt-0.5">
              {item.type === 'chat' ? <MessageSquare className="w-4 h-4 text-brand-700" /> : <Stethoscope className="w-4 h-4 text-blue-700" />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h3 className="text-sm font-bold text-slate-900 truncate">{item.title}</h3>
                <span className="text-[11px] text-slate-400 flex items-center gap-1 flex-shrink-0">
                  <Clock className="w-3 h-3" />
                  <span>{item.date}</span>
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-1">{item.summary}</p>
              <div className="text-[10px] text-slate-400 mt-1">स्रोत: {item.source}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
