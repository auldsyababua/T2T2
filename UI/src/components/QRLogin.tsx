import React, { useState, useEffect } from 'react';
import { startQRLogin, checkQRStatus } from '../lib/api';
import { Loader2 } from 'lucide-react';

interface QRLoginProps {
  onSuccess: () => void;
}

export function QRLogin({ onSuccess }: QRLoginProps) {
  const [qrCode, setQrCode] = useState<string>('');
  const [phoneCodeHash, setPhoneCodeHash] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [status, setStatus] = useState<string>('Initializing...');

  useEffect(() => {
    initQRLogin();
  }, []);

  useEffect(() => {
    if (phoneCodeHash) {
      const interval = setInterval(checkStatus, 2000);
      return () => clearInterval(interval);
    }
  }, [phoneCodeHash]);

  const initQRLogin = async () => {
    try {
      setLoading(true);
      setError('');
      setStatus('Generating QR code...');
      
      const response = await startQRLogin();
      setQrCode(response.qr_code);
      setPhoneCodeHash(response.phone_code_hash);
      setStatus('Scan the QR code with your Telegram app');
      setLoading(false);
    } catch (err: any) {
      setError(err.message || 'Failed to generate QR code');
      setLoading(false);
    }
  };

  const checkStatus = async () => {
    try {
      const response = await checkQRStatus(phoneCodeHash);
      
      if (response.status === 'success') {
        setStatus('Login successful!');
        setTimeout(onSuccess, 1000);
      } else if (response.status === 'expired') {
        setError('QR code expired. Please refresh.');
      }
    } catch (err) {
      // Ignore errors during polling
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="bg-white dark:bg-[#2A2A2A] rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 className="text-2xl font-bold text-center mb-6">
          Login to Telegram
        </h1>
        
        {loading && (
          <div className="flex flex-col items-center">
            <Loader2 className="animate-spin h-8 w-8 text-blue-500 mb-4" />
            <p className="text-gray-600 dark:text-gray-300">{status}</p>
          </div>
        )}
        
        {error && (
          <div className="bg-red-100 dark:bg-red-900/20 border border-red-400 text-red-700 dark:text-red-400 px-4 py-3 rounded mb-4">
            <p>{error}</p>
            <button
              onClick={initQRLogin}
              className="mt-2 text-sm underline hover:no-underline"
            >
              Try again
            </button>
          </div>
        )}
        
        {qrCode && !loading && !error && (
          <div className="flex flex-col items-center">
            <div className="bg-white p-4 rounded-lg mb-4">
              <img src={qrCode} alt="QR Code" className="w-64 h-64" />
            </div>
            <p className="text-center text-gray-600 dark:text-gray-300">
              {status}
            </p>
            <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-2">
              Open Telegram on your phone and scan this code
            </p>
          </div>
        )}
      </div>
    </div>
  );
}