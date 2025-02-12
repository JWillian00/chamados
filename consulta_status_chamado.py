import requests


def verificar_status_chamado(id_chamado, plataforma):
    from rotas import get_headers, CONFIG, PLATAFORMA_MAPEADA


    if plataforma not in PLATAFORMA_MAPEADA:
        return {"error": "Plataforma inválida."}
    
    empresa = PLATAFORMA_MAPEADA[plataforma]
    config = CONFIG[empresa]
    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workitems/{id_chamado}?api-version=7.1"
    
    headers = get_headers(config["token"])
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        chamado_data = response.json()

        estado_chamado = chamado_data.get("fields", {}).get("System.State", "N/A")
        motivo_fechamento = chamado_data.get("fields", {}).get("System.Reason", "N/A")
        data_fechamento = chamado_data.get("fields", {}).get("Microsoft.VSTS.Common.ClosedDate", None)
        usuario_fechamento = chamado_data.get("fields", {}).get("System.ChangedBy", {}).get("displayName", "Desconhecido")

        return {
            "estado_chamado": estado_chamado,
            "motivo_fechamento": motivo_fechamento,
            "data_fechamento": data_fechamento,
            "usuario_fechamento": usuario_fechamento
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Erro ao verificar o status do chamado: {str(e)}"}
