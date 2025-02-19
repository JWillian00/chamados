function consultarChamado() {
    let idChamado = document.getElementById("id-chamado").value;
    let plataforma = document.getElementById("plataforma-consulta").value;
    let loader = document.getElementById("loader");  
    let consultaDados = document.querySelector(".consulta-dados"); 

    loader.style.display = "block";
    consultaDados.style.display = "none";

    fetch("/consultar", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            id_chamado: idChamado,
            plataforma: plataforma
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert("Erro ao consultar o chamado: " + data.error);
        } else {
            
            document.getElementById("titulo").innerText = data.titulo;
            document.getElementById("state").innerText = data.estado_chamado;
            document.getElementById("reason").innerText = data.status;
            document.getElementById("board-column").innerText = data.coluna;
        }

        loader.style.display = "none";
        consultaDados.style.display = "block";
    })
    .catch(error => {
        console.error("Erro ao consultar o chamado:", error);
        loader.style.display = "none"; 
    });
}
