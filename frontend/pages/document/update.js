import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import styles from '../../styles/document.module.css';

// Utility functions
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

const getTokenFromCookies = () => {
    const cookies = document.cookie.split('; ').reduce((acc, cookie) => {
        const [key, value] = cookie.split('=');
        acc[key] = value;
        return acc;
    }, {});
    return cookies.token || null;
};

export default function UpdateDocument() {
    const router = useRouter();
    const [documents, setDocuments] = useState([]);
    const [selectedDocId, setSelectedDocId] = useState('');
    const [docTitle, setDocTitle] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false); // Tambahkan state untuk loading
    const [currentUserEmail, setCurrentUserEmail] = useState('');

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

        // Fetch documents on load
        fetchDocuments(token, decodedToken.sub);
    }, [router]);

    const fetchDocuments = async (token, email) => {
        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/document/list?email=${email}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
            });

            const data = await response.json();
            if (response.ok) {
                // Filter dokumen unik berdasarkan ID
                const uniqueDocuments = data.documents.filter(
                    (doc, index, self) => index === self.findIndex((d) => d.id === doc.id)
                );
                setDocuments(uniqueDocuments);
                setError('');
            } else {
                const errorMessage = Array.isArray(data.detail)
                    ? data.detail.map((err) => `${err.loc.join('.')}: ${err.msg}`).join('\n')
                    : data.detail || 'Unknown error occurred.';
                setError(errorMessage);
            }
        } catch (error) {
            console.error('Error fetching documents:', error);
            setError('Failed to fetch documents.');
        }
    };

    const handleLoadDocument = async (docId) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/document/view/${docId}?email=${currentUserEmail}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
            });

            const data = await response.json();
            if (response.ok) {
                setSelectedDocId(docId);
                setDocTitle(data.title || '');
                setMessage(data.content || '');
                setError('');
            } else {
                setError(data.detail || 'Error loading document.');
            }
        } catch (error) {
            console.error('Error loading document:', error);
            setError('Failed to load document.');
        }
    };

    const handleSaveChanges = async () => {
        if (!selectedDocId || !docTitle || !message) {
            setError('Please fill in all required fields.');
            return;
        }
    
        setIsLoading(true); // Set loading true saat aksi dimulai
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/document/update?email=${currentUserEmail}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    id: selectedDocId,
                    title: docTitle,
                    content: message,
                }),
            });
    
            // Parse response
            const data = await response.json();
    
            if (response.ok) {
                alert('Document updated successfully!');
                setError('');
            } else {
                // Jika ada error detail, tampilkan
                const errorMessage = Array.isArray(data.detail)
                    ? data.detail.map((err) => `${err.loc.join('.')}: ${err.msg}`).join('\n')
                    : data.detail || 'Error saving document.';
                setError(errorMessage);
            }
        } catch (error) {
            console.error('Error saving document:', error);
            setError('Failed to save document. Please check your connection or try again later.');
        } finally {
            setIsLoading(false); // Reset loading status setelah aksi selesai
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

            <h1 className={styles.title}>Update Document</h1>
            <div className={styles.form}>
                <label>Select a Document:</label>
                <select
                    value={selectedDocId}
                    onChange={(e) => handleLoadDocument(e.target.value)}
                    className={styles.input}
                >
                    <option value="" disabled>Select a document</option>
                    {documents.map((doc) => (
                        <option key={doc.id} value={doc.id}>
                            {doc.title}
                        </option>
                    ))}
                </select>

                <label>Document Title:</label>
                <input
                    type="text"
                    placeholder="Enter document title"
                    value={docTitle}
                    onChange={(e) => setDocTitle(e.target.value)}
                    className={styles.input}
                />

                <label>Message:</label>
                <textarea
                    placeholder="Update your message content here..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className={styles.textArea}
                ></textarea>

                {error && (
                    <p className={styles.error}>
                        {typeof error === 'string' ? error : 'An unexpected error occurred'}
                    </p>
                )}

                <div className={styles.actions}>
                    <button
                        className={styles.buttonPrimary}
                        onClick={handleSaveChanges}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>
            </div>
        </div>
    );
}
