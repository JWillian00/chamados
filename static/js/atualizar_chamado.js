
async function atualizarChamado(idChamado) {
    try {
        // Capturar os valores dos campos do modal
        const empresaChamado = document.getElementById('empresa_chamado').value;
        const plataformaChamado = document.getElementById('plataforma_chamado').value;
        const filialChamado = document.getElementById('filial_chamado').value;
        const categoria = document.getElementById('categoria').value;
        const statusChamado = document.getElementById('status_chamado').value;
        const prioridade = document.getElementById('prioridade').value;
        const responsavel = document.getElementById('responsavel').value;

       
        if (!empresaChamado || !plataformaChamado || !filialChamado || !categoria || !statusChamado || !prioridade || !responsavel) {
            alert('Por favor, preencha todos os campos obrigatórios.');
            return;
        }

       
        const dadosAtualizacao = {
            Empresa: empresaChamado,
            Plataforma: plataformaChamado,
            Filial: filialChamado,
            Categoria: categoria,
            Status: statusChamado,
            Prioridade: prioridade,
            Responsavel: responsavel
        };

       
        const { data, error } = await supabase
            .from('chamado')
            .update(dadosAtualizacao)
            .eq('id_chamado', idChamado);

        if (error) {
            console.error('Erro ao atualizar chamado:', error);
            alert('Erro ao atualizar o chamado. Tente novamente.');
        } else {
            console.log('Chamado atualizado com sucesso:', data);
            alert('Chamado atualizado com sucesso!');
            
         
            const modal = document.getElementById('detalhesModal');
            if (modal) {
                const bootstrapModal = bootstrap.Modal.getInstance(modal);
                if (bootstrapModal) {
                    bootstrapModal.hide();
                }
            }
            
            location.reload(); 
        }

    } catch (error) {
        console.error('Erro inesperado:', error);
        alert('Erro inesperado ao atualizar o chamado.');
    }
}

function configurarBotaoSalvar() {
    const botaoSalvar = document.getElementById('btnSalvarChamado');
    if (botaoSalvar) {
        botaoSalvar.addEventListener('click', function() {
            const idChamado = document.getElementById('id_chamado_hidden').value || 
                            document.getElementById('detalhesModal').getAttribute('data-id-chamado');
            
            if (idChamado) {
                atualizarChamado(idChamado);
            } else {
                alert('ID do chamado não encontrado.');
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', function() {
    configurarBotaoSalvar();
});

function salvarChamado() {
    const idChamado = document.getElementById('id_chamado_hidden').value || 
                    document.getElementById('detalhesModal').getAttribute('data-id-chamado');
    
    if (idChamado) {
        atualizarChamado(idChamado);
    } else {
        alert('ID do chamado não encontrado.');
    }
}