import styles from '../styles/navbar.module.css';

export default function Navbar() {
    return (
        <nav className={styles.navbar}>
            <div className={styles.logo}>Future Message</div>
            <ul className={styles.navLinks}>
                <li><a href="/">Home</a></li>
                <li><a href="/auth/login">Login</a></li>
                <li><a href="/auth/signup">Sign Up</a></li>
            </ul>
        </nav>
    );
}
