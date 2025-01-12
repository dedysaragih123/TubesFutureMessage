import { useState } from 'react';
import styles from '../styles/sickleave.module.css';

export default function SickLeaveForm() {
    const [username, setUsername] = useState('');
    const [reason, setReason] = useState('');
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsSubmitting(true);

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/integrate/sick-leave`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, reason, email }),
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to submit sick leave.');
            }

            setMessage('Sick leave submitted successfully!');
        } catch (error) {
            setMessage(error.message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className={styles.container}>
            <h1 className={styles.title}>Create Sick Leave</h1>
            <form className={styles.form} onSubmit={handleSubmit}>
                <label className={styles.label}>Username</label>
                <input
                    type="text"
                    className={styles.input}
                    placeholder="Enter your username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                />

                <label className={styles.label}>Reason</label>
                <textarea
                    className={styles.textArea}
                    placeholder="Enter reason for sick leave"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    required
                ></textarea>

                <label className={styles.label}>Email</label>
                <input
                    type="email"
                    className={styles.input}
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />

                <button
                    type="submit"
                    className={styles.button}
                    disabled={isSubmitting}
                >
                    {isSubmitting ? 'Submitting...' : 'Submit'}
                </button>
            </form>
            {message && <p className={styles.message}>{message}</p>}
        </div>
    );
}
