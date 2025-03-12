import requests
import base64
import os
from enviar_img import upload_to_imgur
from flask import flash, jsonify
from firebase import salvar_chamado
import time


CONFIG = {
    "board_ecomm": {
        "organization": "BRAVEO",
        "project": "E-commerce%20Team",
        "token": "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"
    },
    "board_sustentacao": {
        "organization": "BRAVEO",
        "project": "Click%20Veplex",
        "token": "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"
    },
    "board_bodegamix": {
        "organization": "BRAVEO",
        "project": "Bodegamix",
        "token": "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"
    }
}


PLATAFORMA_MAPEADA = {
    "click": "board_sustentacao",
    "e-commerce": "board_ecomm",
    "E-commerce": "board_ecomm",
    "E-Commerce": "board_ecomm",
    "Click": "board_sustentacao",
    "board_sustentacao": "click",
    "board_ecomm": "e-commerce",
    "board_bodegamix": "Bodegamix",
    "Bodegamix": "board_bodegamix",
    "bodegamix": "board_bodegamix"
    
}
PLATAFORMA_REVERSE_MAPEADA = {
    "board_sustentacao": "click",
    "board_ecomm": "e-commerce",
    "board_bodegamix": "Bodegamix"
}

MAX_FILE_SIZE = 60 * 1024 * 1024 

def upload_file_to_azure(file, config):
    if file.content_length > MAX_FILE_SIZE:
        print("Tamanho do arquivo excede o limite permitido. 60MB")
        return None

    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/attachments?fileName={file.filename}&api-version=7.1-preview.3"

    headers = {
    "Content-Type": "application/octet-stream",
    "Authorization": "Basic " + base64.b64encode(f":{config['token']}".encode('utf-8')).decode('utf-8')
}

    try:
        response = requests.post(url, headers=headers, data=file.read())
        if response.status_code == 201:
            return response.json()["url"]
        else:
            print(f"Erro ao fazer upload: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer upload: {str(e)}")
        return None
    

def consultar_comentarios(id_chamado, plataforma):

    plataforma = plataforma.lower().strip()

    if plataforma in PLATAFORMA_MAPEADA:
        empresa = PLATAFORMA_MAPEADA[plataforma]
    else:
       return {"error": "Plataforma inválida."}	

    config = CONFIG[empresa]
    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workItems/{id_chamado}/comments?api-version=7.1-preview.4"
    
    headers = get_headers(config["token"])

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        comentarios_data = response.json()
        comentarios = comentarios_data.get("comments",[])

        #print("retorno consultar:", comentarios_data)

        comentarios_list = []
        for comentario in comentarios:
            autor = comentario.get("createdBy", {}).get("displayName", "Desconhecido")
            texto_comentario = comentario.get("text", "")
            comentarios_list.append({"autor": autor, "comentario": texto_comentario})

        return jsonify(comentarios_list)
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Erro ao buscar comentários: {str(e)}"}

def get_headers(token):
    encoded_token = base64.b64encode(f":{token}".encode("utf-8")).decode("utf-8")
    return {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"Basic {encoded_token}"
    }
def consultar_chamado(id_chamado, plataforma):
    empresa = PLATAFORMA_MAPEADA.get(plataforma.lower().strip())
    if not empresa:
        return {"error": "Plataforma inválida."}

    config = CONFIG[empresa]
    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workitems/{id_chamado}?api-version=7.1"
    headers = get_headers(config["token"])

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        chamado_data = response.json()
        #print("Retorno Consulta API", chamado_data)

        return {
            "titulo": chamado_data.get("fields", {}).get("System.Title", "Título não encontrado"),
            "estado_chamado": chamado_data.get('fields', {}).get('System.State', "N/A"),
            "status": chamado_data.get('fields', {}).get('System.Reason', "N/A"),
            "coluna": chamado_data.get('fields', {}).get('System.BoardColumn', "N/A"),
            "plataforma": empresa,
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Erro ao consultar o chamado: {str(e)}"}


def create_work_item(titulo, descricao, empresa, plataforma, email, filial, work_item_type="issue", evidencia_files=None):
    empresa_selecionada = empresa.strip()
    
    if plataforma == "e-commerce":        
        if empresa_selecionada not in ["tiscoski", "Oniz"]:
            flash("Apenas as empresas Tiscoski e Oniz podem criar chamados na plataforma E-commerce.", "error")
            return {"error": "Plataforma restrita a empresas Tiscoski e Oniz."}
    elif plataforma == "click":
        #empresa_selecionada = empresa.strip().lower()
        pass   
    

    if plataforma in PLATAFORMA_MAPEADA:
        empresa = PLATAFORMA_MAPEADA[plataforma]
    else:
        return {"error": "Plataforma inválida."}
    #if empresa not in CONFIG:
     #   return {"error": "Empresa inválida, verifique os dados da empresa."}    

    config = CONFIG[empresa]
    
    descricao_com_quebras = descricao.replace("\n", "<br>")

    descricao_formatada = f"""
    <strong>Empresa:</strong> {empresa_selecionada}<br>
    <strong>Plataforma:</strong> {plataforma}<br>
    <strong>E-mail:</strong> {email}<br>
    <strong>Filial:</strong> {filial}<br>
    <strong>Descrição:</strong> {descricao_com_quebras}
    """

    attachment_urls = []
    if evidencia_files:
        for file in evidencia_files:
            file_url = upload_file_to_azure(file, config)
            if file_url:
                attachment_urls.append(file_url)
                descricao_formatada += f'<br><br><strong>Evidência:</strong><br><img src="{file_url}" alt="Evidência" style="max-width: 100%; height: auto;">'


    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
    headers = get_headers(config["token"])

    estado_inicial = "New" #if empresa == "board_sustentacao" else "Doing"

    payload = [
        {"op": "add", "path": "/fields/System.Title", "value": titulo},
        {"op": "add", "path": "/fields/System.Description", "value": descricao_formatada},
        {"op": "add", "path": "/fields/System.State", "value": estado_inicial},
        {"op": "add", "path": "/fields/Custom.Equipe", "value": "TI Digital"},
        #{"op": "add", "path": "/fields/Custom.Unidade", "value": filial}
        #{"op": "add", "path": "/fields/System.BoardLane", "value": "Sustentação"}
    ]

    
    if empresa == "board_sustentacao" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial})
    elif empresa == "board_ecomm" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial})
    elif email == "board_bodegamix" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial})

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        chamado_data = response.json()
        id_chamado = chamado_data.get("id") 

        if id_chamado and attachment_urls:
            for file_url in attachment_urls:
                attach_payload = [{"op": "add", "path": "/relations/-", "value": {"rel": "AttachedFile", "url": file_url}}]
                attach_url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workitems/{id_chamado}?api-version=7.1"
                requests.patch(attach_url, json=attach_payload, headers=headers)

        if response.status_code == 200:
            chamado_data = response.json()
            id_chamado = chamado_data.get("id")
            salvar_chamado(empresa_selecionada, plataforma, email, titulo, descricao, filial, id_chamado)

        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(response.text)
        return {"error": f"Erro ao criar o Chamado!: {str(e)}"}
    
        
def adicionar_comentario_card(id_chamado, comentario, plataforma ): 
   
    plataforma = plataforma.lower().strip()
    print(f"Plataforma recebida: {plataforma}")
    
    if plataforma in PLATAFORMA_MAPEADA:
        empresa = PLATAFORMA_MAPEADA[plataforma]
        print(f"Plataforma convertida: {plataforma}")
    else:
        print(f"Empresa não encontrada para a plataforma: {plataforma}")
        return {"error": "Plataforma inválida."}	

    config = CONFIG[plataforma]   
    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workItems/{id_chamado}/comments?api-version=7.1-preview.4"
    token = config['token']
    authorization_value = f"Basic {base64.b64encode(f':{token}'.encode('utf-8')).decode('utf-8')}"
    headers = {
    "Content-Type": "application/json",
    "Authorization": authorization_value
    }


    payload = {
        "text": comentario
    }
    
    try:       
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()        
        return {"success": True}
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição: {e}")
        print(f"Resposta da API: {response.text}")
        return {"error": f"Erro ao adicionar comentário: {str(e)}"}

