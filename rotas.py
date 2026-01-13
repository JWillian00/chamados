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
         "token": os.environ.get("AZURE_TOKEN_SUSTENTACAO")
    },
    "board_sustentacao": {
        "organization": "BRAVEO",
        "project": "Click%20Veplex",
         "token": os.environ.get("AZURE_TOKEN_SUSTENTACAO")
    },
    "board_bodegamix": {
        "organization": "BRAVEO",
        "project": "BraveoShop",
         "token": os.environ.get("AZURE_TOKEN_SUSTENTACAO")
    },
 
    "azure_devops_unico": {
        "organization": "BRAVEO",
        "project": "Click%20Veplex", 
         "token": os.environ.get("AZURE_TOKEN_SUSTENTACAO")
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
    "board_sustentacao": "board_sustentacao",
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

def consultar_comentarios(id_chamado, plataforma=None): 
    print(f"DEBUG: Plataforma recebida em consultar_comentarios: {plataforma}")

    config = CONFIG.get("azure_devops_unico") 
    if not config:
        print(f"DEBUG: Configuração 'azure_devops_unico' não encontrada.")
        return []

    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workItems/{id_chamado}/comments?api-version=7.1-preview.4"
    token = config['token']
    authorization_value = f"Basic {base64.b64encode(f':{token}'.encode('utf-8' )).decode('utf-8')}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization_value
    }

    try:
        print(f"DEBUG: Fazendo requisição GET para {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"DEBUG: Resposta da API do Azure (comentários): {json.dumps(data, indent=2)}")
        
        comentarios_azure = []
        for comment in data.get('comments', []):
            autor = comment.get('createdBy', {}).get('displayName', 'Desconhecido')
            comentario_texto = comment.get('text', 'Comentário vazio')
            
            comentarios_azure.append({
                "autor": autor,
                "comentario": comentario_texto,
                "data_criacao": comment.get('createdDate'),
                "origem": "Azure DevOps"
            })
        print(f"DEBUG: Comentários do Azure processados: {json.dumps(comentarios_azure, indent=2)}")
        return comentarios_azure
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred in consultar_comentarios: {http_err} - {response.text}" )
    except Exception as e:
        print(f"Erro ao consultar comentários do Azure: {e}")
    return []


def get_headers(token):
    encoded_token = base64.b64encode(f":{token}".encode("utf-8")).decode("utf-8")
    return {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"Basic {encoded_token}"
    }

def consultar_chamado(id_chamado, plataforma):
    if not plataforma:
        return {"error": "Plataforma não informada."}

    if not isinstance(plataforma, str):
        return {"error": "Formato de plataforma inválido."}

    plataforma_formatada = plataforma.lower().strip()
    empresa = PLATAFORMA_MAPEADA.get(plataforma_formatada)

    if not empresa:
        return {"error": f"Plataforma inválida: {plataforma}"}

    config = CONFIG.get(empresa)
    if not config:
        return {"error": f"Configuração da empresa não encontrada para a plataforma '{plataforma}'."}

    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workitems/{id_chamado}?api-version=7.1"
    headers = get_headers(config["token"])

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        chamado_data = response.json()

        print("chamados json ====>", chamado_data)

        if not isinstance(chamado_data, dict):
            return {"error": "Resposta da API Azure está em formato inesperado."}

        fields = chamado_data.get("fields", {})
        if not isinstance(fields, dict):
            return {"error": "Campos do chamado estão mal formatados."}

        return {
            "titulo": fields.get("System.Title", "Título não encontrado"),
            "estado_chamado": fields.get("System.State", "N/A"),
            "status": fields.get("System.Reason", "N/A"),
            "coluna": fields.get("System.BoardColumn", "N/A"),
            "plataforma": empresa,
        }

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Falha ao consultar chamado {id_chamado}: {e}")
        return {"error": f"Erro ao consultar o chamado: {str(e)}"}

    except Exception as e:
        print(f"[ERRO] Erro inesperado em consultar_chamado: {e}")
        return {"error": f"Erro inesperado: {str(e)}"}


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
    plataforma_selecionada = plataforma.strip()

    # Lógica para selecionar o board
    if plataforma_selecionada.lower() == "e-commerce":
        if empresa_selecionada.lower() in ["tiscoski", "oniz"]:
            board_config_key = "board_ecomm"
        else:
            return {"error": "Para a plataforma E-commerce, a empresa deve ser 'Tiscoski' ou 'Oniz'."}
    elif plataforma_selecionada.lower() == "click":
        board_config_key = "board_sustentacao"
    elif plataforma_selecionada.lower() == "bodegamix":
        board_config_key = "board_bodegamix"
    else:
        return {"error": f"Plataforma '{plataforma_selecionada}' é inválida ou não suportada."}

    config = CONFIG.get(board_config_key)
    if not config:
        return {"error": "Configuração da empresa não encontrada para a plataforma selecionada."}

    descricao_com_quebras = descricao.replace("\n", "<br>")
    descricao_formatada = f"""
    <strong>Empresa:</strong> {empresa_selecionada}<br>
    <strong>Plataforma:</strong> {plataforma_selecionada}<br>
    <strong>E-mail:</strong> {email}<br>
    <strong>Filial:</strong> {filial}<br>
    <strong>Descrição:</strong> {descricao_com_quebras}
    """

    # Lista de anexos processados
    attachments_payload = []
    if chamado_anexos:
        print(f"DEBUG: Processando {len(chamado_anexos)} anexos")
        descricao_formatada += "<p><strong>Anexos:</strong></p>"

        for i, anexo_data in enumerate(chamado_anexos):
            link_supabase = ""
            filename = f"Anexo_{i+1}"
            mimetype = "application/octet-stream"

            if isinstance(anexo_data, dict):
                link_supabase = anexo_data.get('url', '')
                filename = anexo_data.get('filename', filename)
                mimetype = anexo_data.get('mimetype', mimetype)
            elif isinstance(anexo_data, str):
                link_supabase = anexo_data
                filename = link_supabase.split("/")[-1] if "/" in link_supabase else filename

            if not link_supabase:
                print(f"❌ URL do anexo {i+1} está vazia.")
                continue

            try:
                file_response = requests.get(link_supabase, timeout=30)
                file_response.raise_for_status()
                file_content = file_response.content

                # Envia o arquivo para o Azure
                azure_attachment_url = upload_file_to_azure(
                    file_content=file_content,
                    config=config,
                    filename=filename,
                    content_type=mimetype
                )

                if azure_attachment_url:
                    # Adiciona o anexo no payload
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

                    # Adiciona a visualização na descrição
                    if is_image_file(filename, mimetype):
                        descricao_formatada += f'<p><strong>{filename}:</strong></p>'
                        descricao_formatada += f'<img src="{azure_attachment_url}" alt="{filename}" style="max-width: 600px; height: auto; border: 1px solid #ddd; margin: 10px 0;"><br>'
                    else:
                        descricao_formatada += f'<p>📎 <strong>{filename}</strong>: <a href="{azure_attachment_url}" target="_blank">Abrir anexo</a></p>'
                else:
                    print(f"⚠️ Falha ao anexar {filename} no Azure.")
                    descricao_formatada += f'<p>❌ Falha ao anexar: {filename}</p>'

            except requests.exceptions.RequestException as e:
                print(f"🚫 Erro ao baixar o anexo {filename}: {e}")
                descricao_formatada += f'<p>❌ Erro ao baixar: {filename} - {str(e)}</p>'
            except Exception as e:
                print(f"🔥 Erro inesperado com anexo {filename}: {e}")
                descricao_formatada += f'<p>❌ Erro inesperado no anexo: {filename}</p>'

    if len(descricao_formatada) > 32000:
        descricao_formatada = descricao_formatada[:31900] + "<p>...Conteúdo truncado devido ao tamanho.</p>"

    url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
    headers = get_headers(config["token"])

    payload = [
        {"op": "add", "path": "/fields/System.Title", "value": titulo},
        {"op": "add", "path": "/fields/System.Description", "value": descricao_formatada},
        {"op": "add", "path": "/fields/System.State", "value": "New"},
        {"op": "add", "path": "/fields/Custom.Equipe", "value": "TI Digital"},
        {"op": "add", "path": "/fields/System.AssignedTo", "value": "Amanda Sobreiro Meneghetti"},
    ]

    if board_config_key == "board_sustentacao" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial}),
        payload.append({"op": "add", "path": "/fields/Custom.Sistemas", "value": "Click"})
    elif board_config_key == "board_ecomm" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial})
    elif board_config_key == "board_bodegamix" and filial:
        payload.append({"op": "add", "path": "/fields/Custom.Unidade", "value": filial}),
        payload.append({"op": "add", "path": "/fields/Custom.Sistemas", "value": "Bodegamix"})
    elif filial == "Oniz" and board_config_key == "board_ecomm":
        payload.append({"op": "add", "path": "/fields/Custom.Sistemas", "value": "E-Commerce Oniz"})
    elif filial == "Tiscoski" and board_config_key == "board_ecomm":
        payload.append({"op": "add", "path": "/fields/Custom.Sistemas", "value": "E-Commerce Tiscoski"})

    sistema_definido = any (
        p["path"] == "/fields/Custom.Sistemas" for p in payload
    )
    if not sistema_definido:
        payload.append({"op": "add", "path": "/fields/Custom.Sistemas", "value": "GSeller"})

    try:
        print(f"DEBUG: Criando work item no Azure DevOps")
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code in (200, 201):
            print("Card criado com sucesso!")
            return response.json()  
        else:
            print(f"Erro ao criar work item: {response.text}")
            return {"error": f"Erro ao criar o work item: {response.text}"}
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar o work item: {e}")
        return {"error": f"Erro ao enviar o work item: {str(e)}"}


def adicionar_comentario_card(id_chamado, comentario, plataforma, anexos=None, nome_usuario=None):
    if not id_chamado or not isinstance(id_chamado, (str, int)):
        return {"error": "ID do chamado inválido."}

    if not comentario or not isinstance(comentario, str):
        return {"error": "Comentário deve ser uma string não vazia."}    

    if not plataforma or not isinstance(plataforma, str):
        return {"error": "Plataforma inválida ou não informada."}

    plataforma = plataforma.lower().strip()
    print(f"[INFO] Plataforma recebida: {plataforma}")

    empresa = PLATAFORMA_MAPEADA.get(plataforma)
    if not empresa:
        print(f"[ERRO] Empresa não encontrada para a plataforma: {plataforma}")
        return {"error": "Plataforma inválida ou não mapeada."}

    config = CONFIG.get(empresa)
    if not config:
        print(f"[ERRO] Configuração não encontrada para empresa: {empresa}")
        return {"error": "Configuração da empresa não encontrada."}

    token = config.get('token')
    if not token:
        return {"error": "Token de autenticação não encontrado na configuração."}

    # URL para adicionar comentário
    comment_url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workItems/{id_chamado}/comments?api-version=7.1-preview.4"
    
    # URL para anexos
    work_item_url = f"https://dev.azure.com/{config['organization']}/{config['project']}/_apis/wit/workItems/{id_chamado}?api-version=7.1"

    authorization_value = f"Basic {base64.b64encode(f':{token}'.encode('utf-8')).decode('utf-8')}"

    headers = {
        "Content-Type": "application/json",
        "Authorization": authorization_value
    }

    comentario_formatado = f"{nome_usuario or 'Usuário do sistema'} comentou via sistema:\n\n{comentario}"
    payload = {"text": comentario_formatado}

    try:
        response = requests.post(comment_url, headers=headers, json=payload)
        response.raise_for_status()
        print(f"[SUCESSO] Comentário adicionado ao chamado {id_chamado}.")

        # Processar anexos
        if anexos:
            attachments_payload = []
            for anexo_data in anexos:
                link_supabase = anexo_data.get('url', '')
                filename = anexo_data.get('filename', 'anexo')
                mimetype = anexo_data.get('mimetype', 'application/octet-stream')

                if link_supabase:
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
                            print(f"[SUCESSO] Anexo {filename} enviado para Azure DevOps.")
                        else:
                            print(f"[ERRO] Falha no upload do anexo: {filename}")
                    except requests.exceptions.RequestException as e:
                        print(f"[ERRO] Erro ao baixar anexo {filename}: {e}")
                    except Exception as e:
                        print(f"[ERRO] Erro inesperado no anexo {filename}: {e}")
            
            if attachments_payload:
                patch_headers = {
                    "Content-Type": "application/json-patch+json",
                    "Authorization": authorization_value
                }
                patch_response = requests.patch(work_item_url, headers=patch_headers, json=attachments_payload)
                patch_response.raise_for_status()
                print(f"[SUCESSO] Anexos adicionados ao work item {id_chamado}.")

        return {"success": True}

    except requests.exceptions.RequestException as e:
        print(f"[ERRO] Requisição falhou: {e}")
        if 'response' in locals():
            print(f"Resposta da API: {response.text}")
        return {"error": f"Erro ao adicionar comentário ou anexos: {str(e)}"}

    except Exception as e:
        print(f"[ERRO] Erro inesperado ao adicionar comentário ou anexos: {e}")
        return {"error": f"Erro inesperado: {str(e)}"}

def obter_estado_chamado_azure(id_chamado_azure):
    config = CONFIG.get("azure_devops_unico")
    if not config:
        return {"error": "Configuração Azure não encontrada."}

    url = (
        f"https://dev.azure.com/{config['organization']}/"
        f"{config['project']}/_apis/wit/workitems/{id_chamado_azure}"
        f"?api-version=7.1"
    )
    headers = get_headers(config["token"])

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        fields = data.get("fields", {})

        return {
            "state": fields.get("System.State"),
            "priority": fields.get("Microsoft.VSTS.Common.Priority"),
            "created_date": fields.get("System.CreatedDate"),
            "changed_date": fields.get("System.ChangedDate"),
            "closed_date": fields.get("Microsoft.VSTS.Common.ClosedDate")
        }

    except requests.exceptions.RequestException as e:
        print(f"Erro ao consultar estado Azure: {e}")
        return {"error": str(e)}