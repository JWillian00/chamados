
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

 
    document.getElementById("comentario-popup").style.display = "block";
    document.getElementById("comentario-popup-overlay").style.display = "block";
    
   
    document.getElementById("comentarios-texto").innerHTML = '';

    
    fetch(`/consultar_comentarios?id_chamado=${idChamado}&plataforma=${plataforma}`)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            const comentariosContainer = document.getElementById('comentarios-texto');
            const comentarios = data.comentarios || []; 

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


function fecharPopupComentario() {
    document.getElementById("comentario-popup").style.display = "none";
    document.getElementById("comentario-popup-overlay").style.display = "none";
}


function enviarComentario() {
    const comentarioTexto = document.getElementById("novo-comentario").value;
    const idChamado = document.getElementById("id-chamado").value; 

    if (!comentarioTexto.trim()) {  
        alert("Por favor, insira um comentário.");
        return;  
    }

    
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
            
            document.getElementById("novo-comentario").value = "";  
            document.getElementById("comentario-popup").style.display = "none"; 
        } else {
            alert("Erro ao adicionar comentário: " + data.error);
        }
    })
    .catch(error => {
        alert("Erro ao enviar comentário: " + error);
    });
}


