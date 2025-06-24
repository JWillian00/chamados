import requests
import base64
import os
from flask import flash, jsonify
import time
import json

CONFIG = {
    "board_ecomm": {
        "organization": "BRAVEO",
        "project": "Tiscoski",
        "token": "1vWWeyzenu0zyYGvqqqWiA1sk3ZBJ6jt3AxB1N7PW6gmJdbSOip3JQQJ99BFACAAAAAxQtTVAAASAZDOnV7b"
    },
    "board_sustentacao": {
        "organization": "BRAVEO",
        "project": "Click%20Veplex",
        "token": "1vWWeyzenu0zyYGvqqqWiA1sk3ZBJ6jt3AxB1N7PW6gmJdbSOip3JQQJ99BFACAAAAAxQtTVAAASAZDOnV7b"
    },
    "board_bodegamix": {
        "organization": "BRAVEO",
        "project": "Bodegamix",
        "token": "1vWWeyzenu0zyYGvqqqWiA1sk3ZBJ6jt3AxB1N7PW6gmJdbSOip3JQQJ99BFACAAAAAxQtTVAAASAZDOnV7b"
    }
}

PLATAFORMA_MAPEADA = {
    "Veplex": "board_sustentacao",
    "Digital": "board_ecomm",
    "digital": "board_ecomm", 
    "veplex": "board_sustentacao",
    "board_sustentacao": "Veplex",
    "board_ecomm": "digital",
    "board_bodegamix": "Globalsys",
    "Globalsys": "board_bodegamix",
    "globalsys": "board_bodegamix"
}

PLATAFORMA_REVERSE_MAPEADA = {
    "board_sustentacao": "Veplex",
    "board_ecomm": "Tiscoski",
    "board_bodegamix": "Globalsys"
}

MAX_FILE_SIZE = 60 * 1024 * 1024 

def upload_file_to_azure(file_content, config, filename, content_type):   
    if len(file_content) > MAX_FILE_SIZE:
        print(f"Tamanho do arquivo {filename} excede o limite permitido (60MB).")
        return None

    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/attachments?fileName={filename}&api-version=7.1-preview.3"

    headers = {
        "Content-Type": "application/octet-stream",
        "Authorization": f"Basic {base64.b64encode(f':{config['token']}'.encode('utf-8')).decode('utf-8')}"
    }
  
    print(f"DEBUG: Headers de upload: {headers}")
    print(f"DEBUG: Fazendo upload do arquivo: {filename}")
    
    try:
        response = requests.post(url, headers=headers, data=file_content)
        print(f"DEBUG: Status do upload: {response.status_code}")
        print(f"DEBUG: Resposta do upload: {response.text}")
        
        if response.status_code == 201:
            return response.json()["url"]
        else:
            print(f"Erro ao fazer upload do anexo {filename}: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição ao fazer upload do anexo {filename}: {str(e)}")
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

        return {
            "titulo": chamado_data.get("fields", {}).get("System.Title", "Título não encontrado"),
            "estado_chamado": chamado_data.get('fields', {}).get('System.State', "N/A"),
            "status": chamado_data.get('fields', {}).get('System.Reason', "N/A"),
            "coluna": chamado_data.get('fields', {}).get('System.BoardColumn', "N/A"),
            "plataforma": empresa,
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Erro ao consultar o chamado: {str(e)}"}

def is_image_file(filename, mimetype):  
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.ico']    
   
    if filename:
        filename_lower = filename.lower()
        if any(filename_lower.endswith(ext) for ext in image_extensions):
            return True    
   
    if mimetype and mimetype.startswith('image/'):
        return True
        
    return False

def create_work_item(titulo, descricao, empresa, plataforma, email, filial="", work_item_type="issue", chamado_anexos=None):   
    empresa_selecionada = empresa.strip()

    if plataforma == "Tiscoski":
        if empresa_selecionada.lower() not in ["tiscoski", "oniz"]:
            flash("Apenas as empresas Tiscoski e Oniz podem criar chamados na plataforma E-commerce.", "error")
            return {"error": "Plataforma restrita a empresas Tiscoski e Oniz."}
    elif plataforma == "Veplex":
        pass
        
    if plataforma in PLATAFORMA_MAPEADA:
        board_config_key = PLATAFORMA_MAPEADA[plataforma]
    else:
        return {"error": "Plataforma inválida ou não mapeada."}

    config = CONFIG.get(board_config_key)
    if not config:
        return {"error": "Configuração da empresa não encontrada para a plataforma selecionada."}

    descricao_com_quebras = descricao.replace("\n", "<br>")

    descricao_formatada = f"""
    <strong>Empresa:</strong> {empresa_selecionada}<br>
    <strong>Plataforma:</strong> {plataforma}<br>
    <strong>E-mail:</strong> {email}<br>
    <strong>Filial:</strong> {filial}<br>
    <strong>Descrição:</strong> {descricao_com_quebras}
    """

    attachments_payload = []  
    if chamado_anexos:
        print(f"DEBUG: Processando {len(chamado_anexos)} anexos")
        descricao_formatada += "<p><strong>Anexos:</strong></p>"
        
        for i, anexo_data in enumerate(chamado_anexos):
            print(f"DEBUG: Processando anexo {i+1}: {anexo_data}")
            
            link_supabase = ""
            filename = "Anexo"
            mimetype = "application/octet-stream"
            
            if isinstance(anexo_data, dict):
                link_supabase = anexo_data.get('url', '')
                filename = anexo_data.get('filename', f'Anexo_{i+1}')
                mimetype = anexo_data.get('mimetype', 'application/octet-stream')
            elif isinstance(anexo_data, str):
                link_supabase = anexo_data
                filename = link_supabase.split("/")[-1] if "/" in link_supabase else f'Anexo_{i+1}'

            if not link_supabase:
                print(f"DEBUG: URL do anexo {i+1} está vazia")
                continue

            try:               
                file_response = requests.get(link_supabase, timeout=30)
                file_response.raise_for_status()
                file_content = file_response.content                
               
                azure_attachment_url = upload_file_to_azure(
                    file_content=file_content,
                    config=config,
                    filename=filename,
                    content_type=mimetype
                )

                if azure_attachment_url:
                   
                    attachments_payload.append({
                        "op": "add",
                        "path": "/relations/-",
                        "value": {
                            "rel": "AttachedFile",
                            "url": azure_attachment_url,
                            "attributes": {
                                "comment": f"Anexo: {filename}"
                            }
                        }
                    })                    
                   
                    is_image = is_image_file(filename, mimetype)
                    
                    if is_image:                        
                        descricao_formatada += f'<p><strong>{filename}:</strong></p>'
                        descricao_formatada += f'<img src="{azure_attachment_url}" alt="{filename}" style="max-width: 600px; height: auto; border: 1px solid #ddd; margin: 10px 0;"><br>'
                    else:                        
                        descricao_formatada += f'<p>📎 Anexo: <a href="{azure_attachment_url}" target="_blank">{filename}</a></p>'
                else:
                    print(f"DEBUG: Falha no upload para Azure do arquivo: {filename}")
                    descricao_formatada += f'<p>❌ Falha ao anexar: {filename}</p>'

            except requests.exceptions.RequestException as e:
                print(f"Erro ao processar anexo {filename}: {e}")
                descricao_formatada += f'<p>❌ Erro ao processar anexo: {filename} - {str(e)}</p>'
            except Exception as e:
                print(f"Erro inesperado ao processar anexo {filename}: {e}")
                descricao_formatada += f'<p>❌ Erro inesperado no anexo: {filename}</p>'
    
    if len(descricao_formatada) > 32000:
        descricao_formatada = descricao_formatada[:31900] + "<p>...Conteúdo truncado devido ao tamanho.</p>"
    
    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
    headers = get_headers(config["token"])

    estado_inicial = "New"

    payload = [
        {"op": "add", "path": "/fields/System.Title", "value": titulo},
        {"op": "add", "path": "/fields/System.Description", "value": descricao_formatada},
        {"op": "add", "path": "/fields/System.State", "value": estado_inicial},
        {"op": "add", "path": "/fields/Custom.Equipe", "value": "TI Digital"},
    ]
   
    payload.extend(attachments_payload)

    if board_config_key == "board_sustentacao" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial})
    elif board_config_key == "board_ecomm" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial})
    elif board_config_key == "board_bodegamix" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial})

    try:
        print(f"DEBUG: Criando work item no Azure DevOps")
        print(f"DEBUG: Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"DEBUG: Status da criação: {response.status_code}")
        print(f"DEBUG: Resposta da criação: {response.text}")
        
        response.raise_for_status()

        chamado_data = response.json()
        id_chamado = chamado_data.get("id")
        
        print(f"DEBUG: Work item criado com sucesso. ID: {id_chamado}")

        return chamado_data

    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar o Chamado no Azure DevOps: {e}")
        if 'response' in locals():
            print(f"Resposta de erro: {response.text}")
        return {"error": f"Erro ao criar o Chamado: {str(e)}"}
    except Exception as e:
        print(f"Erro inesperado ao criar chamado: {e}")
        return {"error": f"Erro inesperado: {str(e)}"}

def adicionar_comentario_card(id_chamado, comentario, plataforma):    
    plataforma = plataforma.lower().strip()
    print(f"Plataforma recebida: {plataforma}")
    
    if plataforma in PLATAFORMA_MAPEADA:
        empresa = PLATAFORMA_MAPEADA[plataforma]
        print(f"Empresa mapeada: {empresa}")
    else:
        print(f"Empresa não encontrada para a plataforma: {plataforma}")
        return {"error": "Plataforma inválida."}

   
    config = CONFIG[empresa]   
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
        if 'response' in locals():
            print(f"Resposta da API: {response.text}")
        return {"error": f"Erro ao adicionar comentário: {str(e)}"}