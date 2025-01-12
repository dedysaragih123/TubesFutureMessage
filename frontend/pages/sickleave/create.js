import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/document.module.css';

// Utility untuk mengambil token dari Local Storage
const getToken = () => localStorage.getItem('token');

export default function CreateSickLeave() {
    const [reason, setReason] = useState('');
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [sickLeaveId, setSickLeaveId] = useState(null);
    const [username, setUsername] = useState('');
    const router = useRouter();

    // Ambil username dari token saat halaman dimuat
    useEffect(() => {
        const token = getToken();
        if (!token) {
            alert('You are not logged in. Redirecting to login page...');
            router.push('/auth/login');
            return;
        }

        try {
            const payload = JSON.parse(atob(token.split('.')[1])); // Decode payload JWT
            setUsername(payload.sub || ''); // Menggunakan `sub` sebagai username
        } catch (err) {
            console.error('Invalid token format:', err);
            alert('Invalid session. Redirecting to login page...');
            router.push('/auth/login');
        }
    }, [router]);

    const handleSubmitSickLeave = async (e) => {
        e.preventDefault();

        const token = getToken();
        if (!token) {
            alert('You are not logged in. Redirecting to login page...');
            router.push('/auth/login');
            return;
        }

        if (!reason.trim()) {
            setError('Reason is required.');
            return;
        }

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/integrate/sick-leave?email=${username}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({ username, reason }),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                console.error('Error:', data);
                setError(data.detail || 'Failed to submit sick leave.');
                return;
            }

            setSuccessMessage('Sick leave request submitted successfully!');
            setSickLeaveId(data.sick_leave_id); // Simpan ID izin sakit dari backend
            setReason('');
            setError('');
        } catch (err) {
            console.error('Error submitting sick leave form:', err);
            setError('An error occurred. Please try again.');
        }
    };

    const handleDownloadPDF = async () => {
        if (!sickLeaveId) {
            alert('Sick leave ID not found. Please create the sick leave form first.');
            return;
        }

        const token = getToken();
        if (!token) {
            alert('You are not logged in. Redirecting to login page...');
            router.push('/auth/login');
            return;
        }

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/integrate/sick-leave-pdf/${sickLeaveId}`,
                {
                    method: 'GET',
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `Sick_Leave_Form_${sickLeaveId}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);
        } catch (err) {
            alert('Failed to download PDF. Please try again.');
        }
    };

    return (
        <div className={styles.container}>
            <nav className={styles.navbar}>
                <div className={styles.navLeft}>
                    <img src="/future-logo.png" alt="Future Message Logo" className={styles.navLogo} />
                    <a href="/" className={styles.navTitle}>Future Message</a>
                </div>
            </nav>

            <h1 className={styles.title}>Create Sick Leave Form</h1>

            {!sickLeaveId ? (
                <form className={styles.form} onSubmit={handleSubmitSickLeave}>
                    <label className={styles.label}>Reason</label>
                    <textarea
                        className={styles.textArea}
                        value={reason}
                        onChange={(e) => setReason(e.target.value)}
                        required
                    ></textarea>

                    {error && <p className={styles.error}>{error}</p>}
                    {successMessage && <p className={styles.success}>{successMessage}</p>}

                    <button type="submit" className={styles.buttonPrimary}>
                        Submit Sick Leave Form
                    </button>
                </form>
            ) : (
                <div className={styles.successContainer}>
                    <p className={styles.success}>
                        Sick leave form submitted successfully! You can now download your form.
                    </p>
                    <button onClick={handleDownloadPDF} className={styles.buttonPrimary}>
                        Download Your Sick Leave Form
                    </button>
                </div>
            )}
        </div>
    );
}
