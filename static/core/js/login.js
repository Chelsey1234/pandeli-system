// Password Toggle
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.getElementById('togglePasswordIcon');
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.replace('fa-eye-slash', 'fa-eye');
    }
}

// Copy credentials (demo credentials panel)
function copyCredentials(username, password) {
    const u = document.getElementById('username');
    const p = document.getElementById('password');
    if (u) u.value = username;
    if (p) p.value = password;
    showCopyToast('Credentials filled in!');
}

function showCopyToast(message) {
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);' +
        'background:#C98A6B;color:#fff;padding:10px 24px;border-radius:30px;' +
        'box-shadow:0 4px 16px rgba(0,0,0,0.2);z-index:9999;font-size:14px;font-weight:500;';
    document.body.appendChild(toast);
    setTimeout(function() { toast.remove(); }, 2000);
}
