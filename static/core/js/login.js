// Password Toggle
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('togglePasswordIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    }
}

// Show Copy Tooltip
function showCopyTooltip(message) {
    // Create tooltip element
    const tooltip = document.createElement('div');
    tooltip.className = 'copy-tooltip animate__animated animate__fadeInUp';
    tooltip.textContent = message;
    tooltip.style.cssText = `
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 10px 20px;
        border-radius: 30px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.2);
        z-index: 9999;
        font-size: 14px;
        font-weight: 500;
    `;
    
    document.body.appendChild(tooltip);
    
    // Remove after 2 seconds
    setTimeout(() => {
        tooltip.classList.add('animate__fadeOutDown');
        setTimeout(() => {
            tooltip.remove();
        }, 500);
    }, 2000);
}

// Form Validation
document.querySelector('.login-form').addEventListener('submit', function(e) {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    
    if (!username || !password) {
        e.preventDefault();
        showCopyTooltip('❌ Please fill in all fields');
    }
});

// Add floating animation to inputs on focus
document.querySelectorAll('.form-control').forEach(input => {
    input.addEventListener('focus', function() {
        this.closest('.form-group').classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
        this.closest('.form-group').classList.remove('focused');
    });
});