from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import base64
import os
from envio_email import enviar_email
     
app = Flask(__name__, template_folder=".", static_folder='image')
app.secret_key = "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB" #key tsk
     
def consultar_chamado(id_chamado):
    organization = "BRAVEO"
    project = "e-Commerce%20Tiscoski"
    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{id_chamado}?api-version=7.1"

    token = "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"
    encoded_token = base64.b64encode(f":{token}".encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded_token}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta um erro em caso de falha na requisição

        data = response.json()
        fields = data.get("fields", {})

        change_by = fields.get("System.ChangedBy", {}).get("displayName", " Não disponível")
        state = fields.get("System.State", "Não disponível")
        reason = fields.get("System.Reason", "Não disponível")
        board_column = fields.get("System.BoardColumn", "Não disponível")

        fechado_por = ""
        if state.lower() == "closed":
            fechado_por = change_by

        # Pegando o histórico de mudanças (comentários)
        #comentarios = fields.get("System.History", [])

        # Se o histórico for uma lista, pegamos o último comentário
        #if isinstance(comentarios, list) and comentarios:
          #  ultimo_comentario = comentarios[-1]  # Último comentário da lista
      #  else:
          #  ultimo_comentario = "Não disponível"

        return {
            "change_by": change_by,
            "fechado_por": fechado_por,
            "state": state,
            "reason": reason,
            "board_column": board_column,
           # "comentarios": ultimo_comentario  # Exibindo apenas o último comentário
        }

    except requests.exceptions.RequestException as e:
        print(f"Erro ao consultar o chamado: {e}")
        return None



def upload_to_imgur(image_file):
    CLIENT_ID = '2bb212b2d974050'
    url = 'https://api.imgur.com/3/upload'
    headers = {'Authorization': f'Client-ID {CLIENT_ID}'}
    
   
    with open(image_file, 'rb') as image:
        files = {'image': image}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        # Retorna a URL da imagem
        return response.json()['data']['link']
    else:
        print(f"Erro ao enviar para o Imgur: {response.text}")
        return None

def create_work_item(titulo, descricao, empresa, plataforma, email):
    organization = "BRAVEO"
    project = "e-Commerce%20Tiscoski"
    work_item_type = "Issue"


    # gambiarra corrigir depois
    descricao_formatada = f"""
    <strong>Empresa:</strong> {empresa}<br>
    <strong>E-mail:</strong> {plataforma}<br>
    <strong>Plataforma:</strong> {email}<br>
    <strong>Descrição:</strong>
    {descricao}
    """

    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/${work_item_type}?api-version=7.1"
    
    token = "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"  
    encoded_token = base64.b64encode(f":{token}".encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"Basic {encoded_token}"
    }

    payload = [
        {"op": "add", "path": "/fields/System.Title", "value": titulo},
        {"op": "add", "path": "/fields/System.Description", "value": descricao_formatada},
        {"op": "add", "path": "/fields/System.State", "value": "Doing"},
        {"op": "add", "path": "/fields/System.AreaPath", "value": "e-commerce Tiscoski"}
    ]

    try:
        response = requests.post(url, json=payload, headers=headers, verify=False)
        response.raise_for_status()  
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar o work item: {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    evidencias = []  
    
    

    if request.method == "POST":
        titulo = request.form["titulo"]
        descricao = request.form["descricao"]
        empresa = request.form["empresa"]  
        plataforma = request.form["plataforma"]  
        email = request.form["email"]

        if not titulo or not descricao or not empresa or not plataforma or not email:
            flash("Título e descrição são obrigatórios.", "error")
            return redirect(url_for("index"))  

        evidencia_files = request.files.getlist("evidencia")
        imgur_links = []  
        img_tags = [] 

        for evidencia_file in evidencia_files:
            if evidencia_file:
                
                app.config['UPLOAD_FOLDER'] = 'uploads'
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], evidencia_file.filename)
                evidencia_file.save(file_path)
                
                
                imgur_link = upload_to_imgur(file_path)
                if imgur_link:
                    
                    img_tag = f'<img src="{imgur_link}" alt="Evidência" style="max-width: 100%; height: auto;">'
                    img_tags.append(img_tag)
                    imgur_links.append(imgur_link)

        
        if img_tags:
            descricao += "\n" + "\n".join(img_tags)  
      
        if imgur_links:
            result = create_work_item(titulo, descricao, empresa, email, plataforma)

            if result:
                id_chamado = result["id"]
                enviar_email(email, id_chamado)
                flash("Work item criado com sucesso!", "success")
                return redirect(url_for("index"))  # if para evitar looping de formulario
            else:
                flash("Erro ao criar o work item. Tente novamente.", "error")
        else:
            flash("Nenhuma evidência foi anexada.", "error")

        return render_template("templates/index.html", evidencias=imgur_links)

    return render_template("templates/index.html", evidencias=evidencias)

@app.route("/consultar/<int:id_chamado>", methods=["GET"])
def consultar(id_chamado):
    # Chama a função que consulta o chamado
    chamado_info = consultar_chamado(id_chamado)
    if chamado_info:
        return chamado_info
    else:
        return {"error": "Chamado não encontrado"}, 404   

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) #utiliza a porta do render para deploy
    app.run(host="0.0.0.0", port=port)
    app.run(debug=True)
    