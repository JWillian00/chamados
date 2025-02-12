// Função para abrir o popup de senha
function abrirPopupSenha() {
    const popupSenha = document.getElementById('senha-popup');
    const overlay = document.getElementById('popup-overlay');
    popupSenha.style.display = 'block';
    overlay.style.display = 'block';
    popupSenha.style.opacity = 0;
    popupSenha.style.transition = "opacity 0.3s ease-in-out";
    setTimeout(() => popupSenha.style.opacity = 1, 10);
}

// Função para fechar o popup de senha
function fecharSenhaPopup() {
    const popupSenha = document.getElementById('senha-popup');
    const overlay = document.getElementById('popup-overlay');
    popupSenha.style.opacity = 0;
    setTimeout(() => {
        popupSenha.style.display = 'none';
        overlay.style.display = 'none';
    }, 300);
}

// Função para validar a senha
function validarSenha() {
    const senha = document.getElementById('senha-input').value;
    if (senha === '132355') {
        window.location.href = 'tela_relatorio.html'; // Redireciona para o relatório
    } else {
        alert('Senha incorreta!');
    }
}
