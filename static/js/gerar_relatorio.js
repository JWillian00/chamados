function gerarRelatorio() {
    // Exibe o loader
    document.getElementById('loading').style.display = 'flex';

    // Captura os valores dos filtros
    let data_inicial = document.querySelector('input[name="data_inicial"]').value;
    let data_final = document.querySelector('input[name="data_final"]').value;

    // Verifica se as datas foram preenchidas
    if (!data_inicial) {
        alert("Por favor, informe a data de abertura do chamado.");
        document.getElementById('loading').style.display = 'none';
        return;
    }

    let filtro_data = document.querySelector('input[name="filtro_data"]:checked') ? document.querySelector('input[name="filtro_data"]:checked').value : '';
    let filial = document.querySelector('input[name="filial"]').value || '';
    let email = document.querySelector('input[name="email"]').value || '';
    let empresa = document.querySelector('input[name="empresa"]').value || '';
    let plataforma = document.querySelector('input[name="plataforma"]').value || '';
    let titulo = document.querySelector('input[name="titulo"]').value || '';

    // Dados para enviar ao backend
    let dados = {
        data_inicial: data_inicial,
        data_final: data_final,
        filtro_data: filtro_data,
        filial: filial,
        email: email,
        empresa: empresa,
        plataforma: plataforma,
        titulo: titulo
    };
    console.log("Dados para enviar ao backend: ", dados);

    // Envia os dados para o backend usando fetch (requisição POST)
    fetch('/relatorio', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Retorno do servidor: ", data);
        document.getElementById('loading').style.display = 'none';

        if (data.error) {
            alert(data.error);
            return;
        }

        // Renderiza os dados na tabela
        let tbody = document.querySelector('tbody');
        tbody.innerHTML = '';
        if (data.chamados && data.chamados.length > 0) {
            data.chamados.forEach(chamado => {
                let row = document.createElement('tr');
                row.innerHTML = `
                    <td>${chamado.id_chamado}</td>
                    <td>${chamado.data_criacao}</td>
                    <td>${chamado.data_fechamento}</td>
                    <td>${chamado.filial}</td>
                    <td>${chamado.email}</td>
                    <td>${chamado.empresa}</td>
                    <td>${chamado.plataforma}</td>
                    <td>${chamado.titulo}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Nenhum dado encontrado</td></tr>';
        }
    })
    .catch(error => {
        document.getElementById('loading').style.display = 'none';
        console.error('Erro ao gerar o relatório:', error);
    });
}
