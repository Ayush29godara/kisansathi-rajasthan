import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Lock, Mail, AlertCircle, Sprout, CheckCircle2 } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { signInWithEmail, signUpWithEmail, signInWithGoogle, signInAsDemoFarmer } = useAuth();

  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const redirectPath = (location.state as any)?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      if (isSignUp) {
        const { error } = await signUpWithEmail(email, password);
        if (error) throw error;
        setSuccessMsg('खाता सफलतापूर्वक बनाया गया! यदि आवश्यक हो तो ईमेल सत्यापन लिंक देखें।');
        setTimeout(() => navigate(redirectPath), 1000);
      } else {
        const { error } = await signInWithEmail(email, password);
        if (error) throw error;
        navigate(redirectPath);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'प्रमाणीकरण विफल रहा';
      setErrorMsg(message);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = async () => {
    setErrorMsg(null);
    try {
      const { error } = await signInWithGoogle();
      if (error) throw error;
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Google लॉगिन विफल रहा';
      setErrorMsg(message);
    }
  };

  return (
    <div className="max-w-md mx-auto my-8 p-6 bg-white rounded-2xl border border-slate-200 shadow-sm">
      <div className="text-center mb-6">
        <div className="w-12 h-12 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center mx-auto mb-3 shadow-inner">
          <Sprout className="w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold text-slate-900">
          {isSignUp ? 'नया किसान खाता बनाएं' : 'किसान साथी लॉगिन'}
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          {isSignUp ? 'राजस्थान किसान सहायता पोर्टल पर पंजीकरण करें' : 'सुरक्षित किसान खाता (Supabase Auth)'}
        </p>
      </div>

      {errorMsg && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">ईमेल पता (Email)</label>
          <div className="relative">
            <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
              placeholder="kisan@example.com"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1">पासवर्ड (Password)</label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:outline-none"
              placeholder="न्यूनतम 6 अक्षर"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 px-4 bg-brand-700 hover:bg-brand-800 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
        >
          {loading
            ? 'प्रक्रिया जारी है...'
            : isSignUp
            ? 'खाता पंजीकृत करें (Sign Up)'
            : 'लॉग इन करें (Sign In)'}
        </button>
      </form>

      <div className="my-4 text-center text-xs text-slate-400">अथवा</div>

      <button
        onClick={handleGoogleAuth}
        type="button"
        className="w-full py-2.5 px-4 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"
      >
        <svg className="w-4 h-4" viewBox="0 0 24 24">
          <path
            fill="#4285F4"
            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
          />
          <path
            fill="#34A853"
            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
          />
          <path
            fill="#FBBC05"
            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
          />
          <path
            fill="#EA4335"
            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
          />
        </svg>
        <span>Google खाते से जारी रखें</span>
      </button>

      <div className="mt-5 text-center text-xs text-slate-600">
        {isSignUp ? 'पहले से खाता है?' : 'क्या आपका खाता नहीं है?'}
        <button
          onClick={() => {
            setIsSignUp(!isSignUp);
            setErrorMsg(null);
            setSuccessMsg(null);
          }}
          className="ml-1 text-brand-700 font-semibold hover:underline"
        >
          {isSignUp ? 'लॉग इन करें' : 'नया खाता बनाएं'}
        </button>
      </div>

      <div className="mt-5 pt-4 border-t border-slate-100">
        <button
          onClick={() => {
            signInAsDemoFarmer();
            navigate(redirectPath);
          }}
          type="button"
          className="w-full py-2.5 px-4 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-800 rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
        >
          <span>⚡ 1-क्लिक डेमो किसान लॉगिन (Instant Demo Access)</span>
        </button>
      </div>
    </div>
  );
};
