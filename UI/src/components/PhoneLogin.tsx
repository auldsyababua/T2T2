import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Loader2, Phone, Shield } from 'lucide-react';

interface PhoneLoginProps {
  onSuccess: (user: any) => void;
}

export const PhoneLogin: React.FC<PhoneLoginProps> = ({ onSuccess }) => {
  const [step, setStep] = useState<'phone' | 'code' | '2fa'>('phone');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Session data from send-code response
  const [phoneCodeHash, setPhoneCodeHash] = useState('');
  const [sessionString, setSessionString] = useState('');

  const handleSendCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      console.log('[PHONE_LOGIN] Sending code to:', phoneNumber);
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://t2t2-production.up.railway.app'}/api/phone-auth/send-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send code');
      }

      const data = await response.json();
      console.log('[PHONE_LOGIN] Code sent successfully');
      
      setPhoneCodeHash(data.phone_code_hash);
      setSessionString(data.session_string);
      setStep('code');
    } catch (err) {
      console.error('[PHONE_LOGIN] Error sending code:', err);
      setError(err.message || 'Failed to send verification code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      console.log('[PHONE_LOGIN] Verifying code');
      
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'https://t2t2-production.up.railway.app'}/api/phone-auth/verify-code`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone_number: phoneNumber,
          code: verificationCode,
          phone_code_hash: phoneCodeHash,
          session_string: sessionString,
          password: password || undefined,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        
        // Check if 2FA is required
        if (error.detail?.includes('Two-factor authentication')) {
          console.log('[PHONE_LOGIN] 2FA required');
          setStep('2fa');
          return;
        }
        
        throw new Error(error.detail || 'Failed to verify code');
      }

      const data = await response.json();
      console.log('[PHONE_LOGIN] Login successful');
      
      // Store the token
      localStorage.setItem('auth_token', data.access_token);
      
      // Call success callback
      onSuccess(data.user);
    } catch (err) {
      console.error('[PHONE_LOGIN] Error verifying code:', err);
      setError(err.message || 'Failed to verify code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Phone className="w-5 h-5" />
          Telegram Authentication
        </CardTitle>
        <CardDescription>
          {step === 'phone' && 'Enter your phone number to receive a verification code'}
          {step === 'code' && 'Enter the verification code sent to your Telegram app'}
          {step === '2fa' && 'Enter your two-factor authentication password'}
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {step === 'phone' && (
          <form onSubmit={handleSendCode} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="phone">Phone Number</Label>
              <Input
                id="phone"
                type="tel"
                placeholder="+1234567890"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                required
                disabled={loading}
              />
              <p className="text-sm text-muted-foreground">
                Include country code (e.g., +1 for US)
              </p>
            </div>
            
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending Code...
                </>
              ) : (
                'Send Verification Code'
              )}
            </Button>
          </form>
        )}

        {step === 'code' && (
          <form onSubmit={handleVerifyCode} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="code">Verification Code</Label>
              <Input
                id="code"
                type="text"
                placeholder="12345"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value)}
                required
                disabled={loading}
                autoFocus
              />
              <p className="text-sm text-muted-foreground">
                Check your Telegram app for the code
              </p>
            </div>
            
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Verify Code'
              )}
            </Button>
            
            <Button
              type="button"
              variant="ghost"
              className="w-full"
              onClick={() => {
                setStep('phone');
                setVerificationCode('');
                setError(null);
              }}
              disabled={loading}
            >
              Use Different Number
            </Button>
          </form>
        )}

        {step === '2fa' && (
          <form onSubmit={handleVerifyCode} className="space-y-4">
            <Alert className="mb-4">
              <Shield className="h-4 w-4" />
              <AlertDescription>
                Two-factor authentication is enabled on your account
              </AlertDescription>
            </Alert>
            
            <div className="space-y-2">
              <Label htmlFor="password">2FA Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                autoFocus
              />
            </div>
            
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Submit Password'
              )}
            </Button>
            
            <Button
              type="button"
              variant="ghost"
              className="w-full"
              onClick={() => {
                setStep('code');
                setPassword('');
                setError(null);
              }}
              disabled={loading}
            >
              Back to Code
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  );
};