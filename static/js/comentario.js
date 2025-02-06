function enviarComentario() {
    const comentarioTexto = document.getElementById("novo-comentario").value;
    const idChamado = document.getElementById("id-chamado").value; // ID do chamado, que você já tem no campo do ID do chamado.

    if (!comentarioTexto.trim()) {  // Verifica se o comentário está vazio ou apenas com espaços
        alert("Por favor, insira um comentário.");
        return;  // Não envia a requisição se o campo estiver vazio
    }

    // Enviar o comentário para o backend
    fetch("/adicionar_comentario", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            id_chamado: idChamado,
            comentario: comentarioTexto
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Comentário adicionado com sucesso!");
            // Fechar o popup ou limpar o campo
            document.getElementById("novo-comentario").value = "";  // Limpa o campo de comentário
            document.getElementById("comentario-popup").style.display = "none";  // Fecha o popup
        } else {
            alert("Erro ao adicionar comentário: " + data.error);
        }
    })
    .catch(error => {
        alert("Erro ao enviar comentário: " + error);
    });
}
