import styles from '../styles/home.module.css';

export default function Home() {
    return (
        <div className={styles.container}>
            {/* Navbar */}
            <nav className={styles.navbar}>
                <div className={styles.logoContainer}>
                    <img src="/future-logo.png" alt="Future Message Logo" className={styles.navLogo} />
                    <span className={styles.navTitle}>Future Message</span>
                </div>
            </nav>

            {/* Hero Section */}
            <header className={styles.hero}>
                <div className={styles.heroContent}>
                    <img src="/future-logo.png" alt="Future Message Logo" className={styles.heroLogo} />
                    <h1 className={styles.heroTitle}>Future Message</h1>
                    <p className={styles.heroSubtitle}>
                        Deliver your words across time. Collaborate, schedule, and connect like never before.
                    </p>
                </div>
            </header>

            {/* Features Section */}
            <main className={styles.main}>
                <section id="features" className={styles.features}>
                    <h2 className={styles.sectionTitle}>Features</h2>
                    <div className={styles.featureCards}>
                        <div className={styles.featureCard}>
                            <h3>Collaborate</h3>
                            <p>
                                Work with friends or colleagues to craft meaningful messages and deliver them together.
                            </p>
                        </div>
                        <div className={styles.featureCard}>
                            <h3>Schedule</h3>
                            <p>
                                Set a specific time to send your message and ensure it arrives when it matters most.
                            </p>
                        </div>
                        <div className={styles.featureCard}>
                            <h3>Stay Connected</h3>
                            <p>
                                Share your thoughts and ideas over time to keep relationships alive and thriving.
                            </p>
                        </div>
                    </div>
                </section>

                {/* Call to Action Section */}
                <section id="cta" className={styles.cta}>
                    <h2>Join Future Message Today</h2>
                    <p className={styles.ctaText}>
                        Take the first step to sending messages across time.
                    </p>
                    <a href="/auth/login" className={styles.ctaButton}>
                        Get Started
                    </a>
                </section>
            </main>

            {/* Footer */}
            <footer className={styles.footer}>
                <p>© 2024 Future Message. Empowering words across time.</p>
            </footer>
        </div>
    );
}
