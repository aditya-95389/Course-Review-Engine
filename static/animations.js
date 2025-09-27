// Modern animations and interactions for CourseHub

// Smooth scroll behavior
document.documentElement.style.scrollBehavior = 'smooth';

// Loading animation for buttons
function addLoadingState(button, text = 'Loading...') {
    const originalText = button.innerHTML;
    button.innerHTML = text;
    button.disabled = true;
    button.style.opacity = '0.7';
    
    return () => {
        button.innerHTML = originalText;
        button.disabled = false;
        button.style.opacity = '1';
    };
}

// Stagger animation for cards
function staggerCards() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Parallax effect for hero section
function initParallax() {
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const hero = document.querySelector('.hero');
        if (hero) {
            hero.style.transform = `translateY(${scrolled * 0.5}px)`;
        }
    });
}

// Floating animation for elements
function addFloatingAnimation(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
        el.style.animation = 'float 3s ease-in-out infinite';
    });
}

// Add CSS for floating animation
const floatingCSS = `
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-10px); }
}

.floating {
    animation: float 3s ease-in-out infinite;
}

.pulse-on-hover:hover {
    animation: pulse 1s infinite;
}

.glow {
    box-shadow: 0 0 20px rgba(102, 126, 234, 0.5);
}

.slide-in-right {
    animation: slideInRight 0.6s ease-out;
}

@keyframes slideInRight {
    from {
        opacity: 0;
        transform: translateX(50px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

.zoom-in {
    animation: zoomIn 0.5s ease-out;
}

@keyframes zoomIn {
    from {
        opacity: 0;
        transform: scale(0.8);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}
`;

// Inject floating CSS
const style = document.createElement('style');
style.textContent = floatingCSS;
document.head.appendChild(style);

// Initialize animations when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add page entrance animation
    document.body.style.opacity = '0';
    document.body.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
        document.body.style.transition = 'all 0.8s ease';
        document.body.style.opacity = '1';
        document.body.style.transform = 'translateY(0)';
    }, 100);
    
    // Initialize other animations
    setTimeout(() => {
        staggerCards();
        initParallax();
        addFloatingAnimation('.nav h1');
    }, 500);
});

// Intersection Observer for scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('slide-in-right');
        }
    });
}, observerOptions);

// Observe elements for scroll animations
setTimeout(() => {
    document.querySelectorAll('.card, .review').forEach(el => {
        observer.observe(el);
    });
}, 1000);

// Enhanced notification system
window.showNotification = function(message, type = 'success', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${type === 'success' ? '✓' : '⚠'}</span>
            <span class="notification-message">${message}</span>
        </div>
    `;
    
    const notificationCSS = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#27ae60' : '#e74c3c'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transform: translateX(400px);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 10000;
            backdrop-filter: blur(10px);
            font-weight: 500;
        }
        
        .notification-content {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .notification-icon {
            font-size: 1.2rem;
        }
    `;
    
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = notificationCSS;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, duration);
};

// Add ripple effect to buttons
function addRippleEffect() {
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON' || e.target.classList.contains('btn')) {
            const button = e.target;
            const ripple = document.createElement('span');
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            if (!document.querySelector('#ripple-styles')) {
                const style = document.createElement('style');
                style.id = 'ripple-styles';
                style.textContent = `
                    @keyframes ripple {
                        to {
                            transform: scale(2);
                            opacity: 0;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
            
            button.style.position = 'relative';
            button.style.overflow = 'hidden';
            button.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        }
    });
}

// Initialize ripple effect
addRippleEffect();