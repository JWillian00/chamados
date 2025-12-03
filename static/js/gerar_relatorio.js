function gerarRelatorio() {

    let data_inicial = document.querySelector('input[name="data_inicial"]').value;
    let data_final = document.querySelector('input[name="data_final"]').value;

    let filtro_data = document.querySelector('input[name="filtro_data"]:checked') ? 
        document.querySelector('input[name="filtro_data"]:checked').value : '';

    let filial = document.querySelector('input[name="filial"]').value.trim();
    let email = document.querySelector('input[name="email"]').value.trim();
    let empresa = document.querySelector('input[name="empresa"]').value.trim();
    let plataforma = document.querySelector('input[name="plataforma"]').value.trim();
    let titulo = document.querySelector('input[name="titulo"]').value.trim();

    if (!data_inicial && !data_final && !filial && !email && !empresa && !plataforma && !titulo) {
        alert("Por favor, preencher os campos de Data Inicial e Data Final para realizar a busca!");
        return; 
    }
    document.getElementById('loading').style.display = 'flex';

    // Dados para enviar ao backend
    let dados = {
        id_chamado_azure: '',
        data_inicial: data_inicial,
        data_final: data_final,
        filtro_data: filtro_data,
        filial_chamado: filial,
        email: email,
        empresa: empresa,
        plataforma: plataforma,
        titulo: titulo
    };
    console.log("Dados para enviar ao backend: ", dados);

    fetch('/relatorio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
    })
    .then(async response => {
        document.getElementById('loading').style.display = 'none';
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            const msg = payload.error || `Erro ${response.status}`;
            alert(msg);
            return;
        }
        const data = payload;

        let tbody = document.getElementById('tbody-relatorio');
        tbody.innerHTML = '';
        if (data.chamados && data.chamados.length > 0) {
            data.chamados.forEach(chamado => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${chamado.id_chamado_azure || ''}</td>
                    <td>${chamado.data_criacao || ''}</td>
                    <td>${chamado.data_fechamento || ''}</td>
                    <td>${chamado.filial || ''}</td>
                    <td>${chamado.email || ''}</td>
                    <td>${chamado.empresa || ''}</td>
                    <td>${chamado.plataforma || ''}</td>
                    <td>${chamado.titulo || ''}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align:center">Nenhum dado encontrado</td></tr>';
        }
    })
    .catch(err => {
        document.getElementById('loading').style.display = 'none';
        console.error('Erro ao gerar o relatório:', err);
        alert('Erro ao comunicar com o servidor.');
    });
}
