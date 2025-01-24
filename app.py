from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import base64
import os

app = Flask(__name__)
app.secret_key = "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"


UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def create_work_item(titulo, descricao):
    organization = "BRAVEO"
    project = "e-Commerce%20Tiscoski"
    work_item_type = "Issue"

    url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/${work_item_type}?api-version=6.0"
    
    token = "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"  
    encoded_token = base64.b64encode(f":{token}".encode("utf-8")).decode("utf-8")

    headers = {
        "Content-Type": "application/json-patch+json",
        "Authorization": f"Basic {encoded_token}"
    }

    payload = [
        {"op": "add", "path": "/fields/System.Title", "value": titulo},
        {"op": "add", "path": "/fields/System.Description", "value": descricao},
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
        
      
        if not titulo or not descricao:
            flash("Título e descrição são obrigatórios.", "error")
            return redirect(url_for("index"))

        
        evidencia_files = request.files.getlist("evidencia")

        
        for evidencia_file in evidencia_files:
            if evidencia_file:
               
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], evidencia_file.filename)
                evidencia_file.save(file_path)
               
                descricao += f"\nEvidência anexada: {file_path}"
                evidencias.append(evidencia_file.filename)  

        result = create_work_item(titulo, descricao)

        if result:
            flash("Work item criado com sucesso!", "success")
        else:
            flash("Erro ao criar o work item. Tente novamente.", "error")

       
        return render_template("formulario.html", evidencias=evidencias)

    return render_template("formulario.html", evidencias=evidencias)

if __name__ == "__main__":
    app.run(debug=True)
