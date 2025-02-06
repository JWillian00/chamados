// Função para abrir o popup
function openPopup() {
    // Exibe o overlay e o popup
    document.getElementById('popup').style.display = 'block';
    document.getElementById('popup-overlay').style.display = 'block';
}

// Função para fechar o popup
function closePopup() {
    // Oculta o overlay e o popup
    document.getElementById('popup').style.display = 'none';
    document.getElementById('popup-overlay').style.display = 'none';
}

// Função de consultar o chamado (opcional)
function consultarChamado() {
    const idChamado = document.getElementById('id-chamado').value;
    const plataforma = document.getElementById('plataforma-consulta').value;

    // Adicione lógica para consultar o chamado aqui, como uma requisição AJAX.
    console.log(`Consultando chamado com ID: ${idChamado} e plataforma: ${plataforma}`);
}
