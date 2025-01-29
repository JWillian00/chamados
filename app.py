from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import base64
import os

app = Flask(__name__, template_folder=".", static_folder='image')
app.secret_key = "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Função para enviar imagem ao Imgur
def upload_to_imgur(image_file):
    CLIENT_ID = '2bb212b2d974050'  
    url = 'https://api.imgur.com/3/upload'
    headers = {'Authorization': f'Client-ID {CLIENT_ID}'}
    
    # Enviar o arquivo para o Imgur
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

    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/${work_item_type}?api-version=6.0"
    
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
    evidencias = []  # Lista para armazenar os links das imagens do Imgur
    
    

    if request.method == "POST":
        titulo = request.form["titulo"]
        descricao = request.form["descricao"]
        empresa = request.form["empresa"]  # Captura a empresa selecionada
        plataforma = request.form["plataforma"]  # Captura a plataforma
        email = request.form["email"]

        if not titulo or not descricao or not empresa or not plataforma or not email:
            flash("Título e descrição são obrigatórios.", "error")
            return redirect(url_for("index"))  # Retorna para a mesma página

        evidencia_files = request.files.getlist("evidencia")
        imgur_links = []  # Lista para armazenar as URLs das imagens
        img_tags = []  # Lista para armazenar as tags <img>

        for evidencia_file in evidencia_files:
            if evidencia_file:
                # Salvar o arquivo temporariamente
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], evidencia_file.filename)
                evidencia_file.save(file_path)
                
                # Enviar o arquivo para o Imgur e obter o link
                imgur_link = upload_to_imgur(file_path)
                if imgur_link:
                    # Adiciona a tag <img> diretamente para exibir a imagem
                    img_tag = f'<img src="{imgur_link}" alt="Evidência" style="max-width: 100%; height: auto;">'
                    img_tags.append(img_tag)
                    imgur_links.append(imgur_link)

        # Adiciona todas as tags de imagem à descrição
        if img_tags:
            descricao += "\n" + "\n".join(img_tags)  
      
        if imgur_links:
            result = create_work_item(titulo, descricao, empresa, email, plataforma)

            if result:
                flash("Work item criado com sucesso!", "success")
                return redirect(url_for("index"))  # Redireciona para evitar reenvio do formulário
            else:
                flash("Erro ao criar o work item. Tente novamente.", "error")
        else:
            flash("Nenhuma evidência foi anexada.", "error")

        return render_template("index.html", evidencias=imgur_links)

    return render_template("index.html", evidencias=evidencias)
   

if __name__ == "__main__":
    #app.run(debug=True)
    pass