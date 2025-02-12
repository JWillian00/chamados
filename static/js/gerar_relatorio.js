function gerarRelatorio() {
    // Exibe o loading
    document.getElementById('loading').style.display = 'flex';

    // Coleta os dados dos filtros do formulário
    let data_inicial = document.querySelector('input[name="data_inicial"]').value || '';
    let data_final = document.querySelector('input[name="data_final"]').value || '';
    let filtro_data = document.querySelector('input[name="filtro_data"]:checked') ? document.querySelector('input[name="filtro_data"]:checked').value : '';
    let filial = document.querySelector('input[name="filial"]').value || '';
    let email = document.querySelector('input[name="email"]').value || '';
    let empresa = document.querySelector('input[name="empresa"]').value || '';
    let plataforma = document.querySelector('input[name="plataforma"]').value || '';
    let titulo = document.querySelector('input[name="titulo"]').value || '';

    // Cria um objeto com os dados coletados
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
        document.getElementById('loading').style.display = 'none';

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
