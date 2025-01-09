import styles from '../styles/dashboard.module.css';
import { useRouter } from 'next/router';

export default function Dashboard() {
    const router = useRouter();

    const handleNavigation = (path) => {
        router.push(path);
    };

    return (
        <div className={styles.container}>
            {/* Header Navigasi */}
            <nav className={styles.navbar}>
                <div className={styles.navLeft}>
                    <img src="/future-logo.png" alt="Future Message Logo" className={styles.navLogo} />
                    <a href="/" className={styles.navTitle}>Future Message</a>
                </div>
                <a href="/" className={styles.navLink}>Back to Home</a>
            </nav>

            {/* Dashboard Pilihan */}
            <div className={styles.dashboardContainer}>
                <h1 className={styles.title}>Your Dashboard</h1>
                <p className={styles.subtitle}>Select an option to get started:</p>

                <div className={styles.options}>
                    <div
                        className={styles.optionCard}
                        onClick={() => handleNavigation('/document/create')}
                    >
                        <img src="/icons/create-icon.png" alt="Create Icon" className={styles.icon} />
                        <h2>Create a New Document</h2>
                        <p>Start a new collaborative document.</p>
                    </div>

                    <div
                        className={styles.optionCard}
                        onClick={() => handleNavigation('/document/update')}
                    >
                        <img src="/icons/update-icon.png" alt="Update Icon" className={styles.icon} />
                        <h2>Update an Existing Document</h2>
                        <p>Edit and refine an existing document.</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
