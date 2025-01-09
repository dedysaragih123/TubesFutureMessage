import { useState } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/auth.module.css';

export default function Signup() {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const router = useRouter();

    const handleSignup = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/signup`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, password }),
            });

            const data = await response.json();

            if (response.status === 500) {
                setError('Email is already registered. Please use another email or log in.');
                return;
            }

            if (!response.ok) {
                setError(data.detail || 'Signup failed');
                return;
            }

            // Redirect ke halaman login
            router.push('/auth/login');
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

            {/* Form Sign Up */}
            <div className={styles.authContainer}>
                <div className={styles.logoContainer}>
                    <img src="/future-logo.png" alt="Future Message Logo" className={styles.logo} />
                </div>
                <form className={styles.form} onSubmit={handleSignup}>
                    <label className={styles.label}>Name</label>
                    <input
                        type="text"
                        placeholder="Enter your name"
                        className={styles.input}
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
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
                    <button type="submit" className={styles.button}>Sign Up</button>
                </form>
                <p className={styles.redirectText}>
                    Already have an account?{' '}
                    <a href="/auth/login" className={styles.link}>
                        Log in here
                    </a>
                </p>
            </div>
        </div>
    );
}
