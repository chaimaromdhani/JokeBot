import React, { useState } from 'react';
import './LoginPage.css'; 

const LoginPage = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();

    const validEmail = 'chaima@gmail.com';
    const validPassword = '123456';

    if (email === validEmail && password === validPassword) {
      setStatus('✅ Login successful!');
      onLoginSuccess();
    } else {
      setStatus('❌ Invalid email or password.');
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <img src="/logo.png" alt="App Logo" className="app-logo1" />
        <form onSubmit={handleLogin} className="login-form">
          <h2>Login</h2>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="login-input"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="login-input"
            required
          />
          <button type="submit" className="login-button">Login</button>
          {status && <p className="login-status">{status}</p>}
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
