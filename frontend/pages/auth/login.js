import { useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/auth.module.css';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const router = useRouter();

    const handleLogin = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.status === 404) {
                // Email tidak terdaftar
                setError('The email you entered is not registered.');
                return;
            }
    
            if (response.status === 401) {
                // Password salah
                setError('The password you entered is incorrect.');
                return;
            }
            
            if (!response.ok) {
                setError(data.detail || 'Login failed');
                return;
            }

            // Simpan token ke localStorage
            localStorage.setItem('token', data.access_token);

            // Redirect ke halaman dashboard
            router.push('/dashboard');
        } catch (err) {
            setError('An error occurred. Please try again.');
            console.error(err);
        }
    };

    return (
        <div className={styles.container}>
            {/* Header Navigasi */}
            <nav className={styles.navbar}>
                <a href="/" className={styles.navLink}>Back to Home</a>
            </nav>

            {/* Form Login */}
            <div className={styles.authContainer}>
                <div className={styles.logoContainer}>
                    <img src="/future-logo.png" alt="Future Message Logo" className={styles.logo} />
                </div>
                <form className={styles.form} onSubmit={handleLogin}>
                    <label className={styles.label}>Email</label>
                    <input
                        type="email"
                        placeholder="Enter your email"
                        className={styles.input}
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                    <label className={styles.label}>Password</label>
                    <input
                        type="password"
                        placeholder="Enter your password"
                        className={styles.input}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                    {error && <p className={styles.error}>{error}</p>}
                    <button type="submit" className={styles.button}>Log In</button>
                </form>
                <p className={styles.redirectText}>
                    Don't have an account?{' '}
                    <a href="/auth/signup" className={styles.link}>
                        Sign up here
                    </a>
                </p>
            </div>
        </div>
    );
}
