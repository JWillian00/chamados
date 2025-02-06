
function openPopup() {
    
    document.getElementById('popup').style.display = 'block';
    document.getElementById('popup-overlay').style.display = 'block';
}


function closePopup() {
    
    document.getElementById('popup').style.display = 'none';
    document.getElementById('popup-overlay').style.display = 'none';
}


function consultarChamado() {
    const idChamado = document.getElementById('id-chamado').value;
    const plataforma = document.getElementById('plataforma-consulta').value;

    if (!idChamado || !plataforma) {
        alert('Por favor, informe o ID do chamado e a plataforma.');
        return;
    }

    fetch('/consultar',{
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id_chamado: idChamado,
            plataforma: plataforma
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            const { titulo, estado_chamado, status, coluna } = data;
            console.log(`Título: ${titulo}, Estado: ${estado_chamado}, Status: ${status}, Coluna: ${coluna}`);
            buscarComentarios(idChamado, plataforma);
        }
    })
    .catch(error => {
        console.error('Erro ao consultar o chamado:', error);
    });
    
    console.log(`Consultando chamado com ID: ${idChamado} e plataforma: ${plataforma}`);
}

function buscarComentarios(idChamado, plataforma) {
    fetch(`/consultar_comentarios?id_chamado=${idChamado}&plataforma=${plataforma}`)
    .then(response => response.json())
    .then(data => {
        const comentariosContainer = document.getElementById('comentarios-texto');
        comentariosContainer.innerHTML = '';

        if (data.error) {
            alert(data.error);
        } else {
            const comentarios = data.comentarios;
            if (comentarios.length > 0) {
                comentarios.forEach(comentario => {
                    comentariosContainer.innerHTML += `<strong>${comentario.autor}:</strong> ${comentario.comentario}`;
                });
                document.getElementById("VerComentarios").style.display = false;
            } else {
                document.getElementById("VerComentarios").style.display = true;
            }
        }
    })
    .catch(error => {
        console.error('Erro ao buscar comentários:', error);
    });
            }




function abrirPopupComentario() {
    const idChamado = document.getElementById('id-chamado').value;
    const plataforma = document.getElementById('plataforma-consulta').value;

    if (!idChamado || !plataforma) {
        alert('Por favor, informe o ID do chamado e a plataforma.');
        return;
    }

    // Exibe o popup
    document.getElementById("comentario-popup").style.display = "block";
    document.getElementById("comentario-popup-overlay").style.display = "block";
    
    // Limpa os comentários antigos ao abrir o popup
    document.getElementById("comentarios-texto").innerHTML = '';

    // Faz a busca dos comentários através da API
    fetch(`/consultar_comentarios?id_chamado=${idChamado}&plataforma=${plataforma}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            const comentariosContainer = document.getElementById('comentarios-texto');
            const comentarios = data.comentarios || []; // Garantir que existe um array de comentários

            if (comentarios.length > 0) {
                comentarios.forEach(comentario => {
                    comentariosContainer.innerHTML += `<p><strong>${comentario.autor}:</strong> ${comentario.comentario}</p>`;
                });
            } else {
                comentariosContainer.innerHTML = "<p>Nenhum comentário encontrado.</p>";
            }
        }
    })
    .catch(error => {
        console.error('Erro ao buscar comentários:', error);
    });
}

// Função para fechar o popup de comentários
function fecharPopupComentario() {
    document.getElementById("comentario-popup").style.display = "none";
    document.getElementById("comentario-popup-overlay").style.display = "none";
}

// Função para enviar comentário (simulação)
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


