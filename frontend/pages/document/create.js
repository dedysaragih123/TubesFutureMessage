import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/document.module.css';

// Utility untuk mendekode JWT token
const decodeToken = (token) => {
    try {
        const payload = token.split('.')[1];
        const decodedPayload = atob(payload);
        return JSON.parse(decodedPayload);
    } catch (error) {
        console.error('Error decoding token:', error);
        return null;
    }
};

// Utility untuk mengambil token dari Cookies
const getTokenFromCookies = () => {
    const cookies = document.cookie.split('; ').reduce((acc, cookie) => {
        const [key, value] = cookie.split('=');
        acc[key] = value;
        return acc;
    }, {});
    return cookies.token || null;
};

export default function CreateDocument() {
    const router = useRouter();
    const [docTitle, setDocTitle] = useState('');
    const [message, setMessage] = useState('');
    const [deliveryDate, setDeliveryDate] = useState('');
    const [collaborators, setCollaborators] = useState([]);
    const [newCollaborator, setNewCollaborator] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [currentUserEmail, setCurrentUserEmail] = useState('');

    // Ambil token dan email pengguna saat komponen dimount
    useEffect(() => {
        let token = localStorage.getItem('token');
        if (!token) {
            token = getTokenFromCookies();
            if (token) {
                localStorage.setItem('token', token);
            }
        }

        if (!token) {
            alert('User not logged in. Redirecting to login page.');
            router.push('/auth/login');
            return;
        }

        const decodedToken = decodeToken(token);
        if (!decodedToken || !decodedToken.sub) {
            alert('Invalid token. Redirecting to login page.');
            localStorage.removeItem('token');
            router.push('/auth/login');
            return;
        }

        setCurrentUserEmail(decodedToken.sub);
    }, [router]);

    const handleAddCollaborator = async () => {
        if (!newCollaborator.trim()) {
            setError('Email is required.');
            return;
        }

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/validate-collaborator/${newCollaborator}`,
                {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                }
            );

            const data = await response.json();
            if (!response.ok || !data.valid) {
                setError(data.message || 'User not found.');
                return;
            }

            if (!collaborators.includes(newCollaborator)) {
                setCollaborators([...collaborators, newCollaborator]);
                setNewCollaborator('');
                setError('');
                alert(`Collaborator ${newCollaborator} added successfully!`);
            } else {
                setError('Collaborator already added.');
            }
        } catch (error) {
            console.error('Error validating collaborator:', error);
            setError('Failed to validate collaborator. Please try again.');
        }
    };

    const handleScheduleAndSend = async () => {
        if (isSubmitting) return;

        if (!docTitle.trim() || !message.trim() || !deliveryDate || collaborators.length === 0) {
            alert('All fields are required, and at least one collaborator must be added.');
            return;
        }

        setIsSubmitting(true);

        const token = localStorage.getItem('token') || getTokenFromCookies();
        if (!token) {
            alert('User not logged in. Redirecting to login page.');
            router.push('/auth/login');
            return;
        }
        const formattedDeliveryDate = `${deliveryDate}T00:00:00`;

        const payload = {
            title: docTitle.trim(),
            content: message.trim(),
            delivery_date: formattedDeliveryDate,
            collaborators,
        };

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_API_URL}/api/v1/document/create?email=${currentUserEmail}`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(payload),
                }
            );

            const data = await response.json();
            if (!response.ok) {
                const errorMessage = Array.isArray(data.detail)
                    ? data.detail.map((err) => `${err.loc.join('.')}: ${err.msg}`).join('\n')
                    : data.detail || 'Unknown error';
                throw new Error(errorMessage);
            }

            alert(data.message);
            setDocTitle('');
            setMessage('');
            setDeliveryDate('');
            setCollaborators([]);
        } catch (error) {
            console.error('Error creating document:', error);
            alert(`Failed to create document: ${error.message || error}`);
        } finally {
            setIsSubmitting(false);
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

            <div className={styles.formContainer}>
                <h1 className={styles.title}>Create a New Document</h1>
                <div className={styles.form}>
                    <label className={styles.label}>Document Title:</label>
                    <input
                        type="text"
                        placeholder="Enter document title"
                        value={docTitle}
                        onChange={(e) => setDocTitle(e.target.value)}
                        className={styles.input}
                    />

                    <label className={styles.label}>Message:</label>
                    <textarea
                        placeholder="Write your message here..."
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        className={styles.textArea}
                    ></textarea>

                    <label className={styles.label}>Delivery Date:</label>
                    <input
                        type="date"
                        value={deliveryDate}
                        onChange={(e) => setDeliveryDate(e.target.value)}
                        className={styles.input}
                    />

                    <label className={styles.label}>Add Collaborators:</label>
                    <div className={styles.collaboratorInput}>
                        <input
                            type="email"
                            placeholder="Enter collaborator's email"
                            value={newCollaborator}
                            onChange={(e) => setNewCollaborator(e.target.value)}
                            className={`${styles.input} ${error ? styles.inputError : ''}`}
                        />
                        <button onClick={handleAddCollaborator} className={styles.button}>
                            Add
                        </button>
                    </div>
                    {error && <p className={styles.error}>{error}</p>}

                    <div className={styles.collaboratorsList}>
                        {collaborators.map((email, index) => (
                            <span key={index} className={styles.collaborator}>
                                {email}
                            </span>
                        ))}
                    </div>

                    <div className={styles.actions}>
                        <button
                            className={styles.buttonPrimary}
                            onClick={handleScheduleAndSend}
                            disabled={isSubmitting}
                        >
                            {isSubmitting ? 'Submitting...' : 'Schedule and Send'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
