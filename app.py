from flask import Flask, request, render_template, flash, redirect, url_for, jsonify, Response
from rotas import create_work_item, consultar_chamado
from envio_email import enviar_email
import os
from enviar_img import upload_to_imgur
from deep_translator import GoogleTranslator
from rotas import consultar_comentarios, adicionar_comentario_card
from gerar_relatorio import gerar_relatorio
from firebase import db

app = Flask(__name__)
app.secret_key = "FlBjRLlDfm2uwNK4m4FOPo7svTs19Yl4oKzcAt1ohQO8I14KfQNuJQQJ99BAACAAAAAxQtTVAAASAZDOJyRB"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        empresa = request.form.get("empresa")
        plataforma = request.form.get("plataforma")
        email = request.form.get("email")
        titulo = request.form.get("titulo2")
        descricao = request.form.get("descricao")
        evidencia_files = request.files.getlist('evidencia')
        filial = request.form.get("filial")

        print(f"Empresa: {empresa}, Plataforma: {plataforma}, E-mail: {email}, Título: {titulo}, Descrição: {descricao}")

       
        imgur_links = []

       
        if not email or not titulo or not descricao:
            flash("E-mail, título e descrição são obrigatórios.", "error")
            return redirect(url_for("index"))
        
        for evidencia_file in evidencia_files:
            if evidencia_file:
                
                app.config['UPLOAD_FOLDER'] = 'uploads'
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], evidencia_file.filename)
                evidencia_file.save(file_path)

                
                imgur_link = upload_to_imgur(file_path)
                if imgur_link and imgur_link not in imgur_links:
                    imgur_links.append(imgur_link)
                os.remove(file_path)

        
        if imgur_links:
            descricao += "<br><br>" + "<br>".join([f'<img src="{link}" alt="Evidência" style="max-width: 100%; height: auto;">' for link in imgur_links])

        
        result = create_work_item(titulo, descricao, empresa, plataforma, email, filial)
        print("Resultado da criação", result)

        if isinstance(result, dict) and "error" in result:
            flash(result["error"], "error")
        else:
            flash(f"Chamado criado com sucesso! ID: {result.get('id')}", "success")
            if result:
                id_chamado = result.get("id")
                enviar_email(email, id_chamado)
                return redirect(url_for("index"))

        return redirect(url_for("index"))

    return render_template("index.html")

@app.route("/aberturaChamado", methods=["GET", "POST"])
def abertura():
    if request.method == "POST":
        empresa = request.form.get("empresa")
        plataforma = request.form.get("plataforma")
        email = request.form.get("email")
        titulo = request.form.get("titulo2")
        descricao = request.form.get("descricao")
        evidencia_files = request.files.getlist('evidencia')
        filial = request.form.get("filial")

        print(f"Empresa: {empresa}, Plataforma: {plataforma}, E-mail: {email}, Título: {titulo}, Descrição: {descricao}")

       
        imgur_links = []

       
        if not email or not titulo or not descricao:
            flash("E-mail, título e descrição são obrigatórios.", "error")
            return redirect(url_for("abertura"))
        
        for evidencia_file in evidencia_files:
            if evidencia_file:
                
                app.config['UPLOAD_FOLDER'] = 'uploads'
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], evidencia_file.filename)
                evidencia_file.save(file_path)

                
                imgur_link = upload_to_imgur(file_path)
                if imgur_link and imgur_link not in imgur_links:
                    imgur_links.append(imgur_link)
                os.remove(file_path)

        
        if imgur_links:
            descricao += "<br><br>" + "<br>".join([f'<img src="{link}" alt="Evidência" style="max-width: 100%; height: auto;">' for link in imgur_links])

        
        result = create_work_item(titulo, descricao, empresa, plataforma, email, filial)
        print("Resultado da criação", result)

        if isinstance(result, dict) and "error" in result:
            flash(result["error"], "error")
        else:
            flash(f"Chamado criado com sucesso! ID: {result.get('id')}", "success")
            if result:
                id_chamado = result.get("id")
                enviar_email(email, id_chamado)
                return redirect(url_for("abertura"))

        return redirect(url_for("abertura"))

    return render_template("index.html")


@app.route("/consultar", methods=["POST"])
def consultar_chamado_route():
    data = request.get_json()
    id_chamado = data.get("id_chamado")
    plataforma = data.get("plataforma")

    if not id_chamado or not plataforma:
        return jsonify({"error": "ID do chamado e plataforma são obrigatórios."})

   
    resultado = consultar_chamado(id_chamado, plataforma)
    

    if "error" in resultado:
        return jsonify({"error": resultado["error"]})
    else:
        
        try:
            dados = {
                "titulo": GoogleTranslator(source='auto', target='pt').translate(resultado.get("titulo", "N/A")),
                "estado_chamado": GoogleTranslator(source='auto', target='pt').translate(resultado.get("estado_chamado", "N/A")),
                "status": GoogleTranslator(source='auto', target='pt').translate(resultado.get("status", "N/A")),
                "coluna": GoogleTranslator(source='auto', target='pt').translate(resultado.get("coluna", "N/A")),
            }
        except Exception as e:
            return jsonify({"error": f"Erro ao traduzir: {str(e)}"})
        print(dados)
        return jsonify(dados)
@app.route("/consultar_comentarios", methods=["GET"])
def consultar_comentarios_route():
    id_chamado = request.args.get("id_chamado")
    plataforma = request.args.get("plataforma")

    if not id_chamado or not plataforma:
        return jsonify({"error": "ID do chamado e plataforma são obrigatórios."})

    resultado = consultar_comentarios(id_chamado, plataforma)

    if isinstance(resultado, Response):
        
        resultado = resultado.json
        
    if isinstance(resultado, list):
        return jsonify({"comentarios": resultado})

    if isinstance(resultado, dict) and "error" in resultado:
        return jsonify({"error": resultado(["error"])})
    else:
        return jsonify({"comentarios": resultado.get("comentarios", [])})
    

@app.route("/adicionar_comentario", methods=["POST"])
def adicionar_comentario():
    
    data = request.get_json()
    id_chamado = data.get("id_chamado")
    comentario = data.get("comentario")
    plataforma = data.get("plataforma")

    if not comentario:
        return jsonify({"error": "Escreva um comentário."})

    resultado = adicionar_comentario_card(id_chamado, comentario, plataforma)

    if "error" in resultado:
        return jsonify({"error": resultado["error"]})
    else:
        return jsonify({"mensagem": "Comentário adicionado com sucesso!"})
    
@app.route('/relatorio', methods=['GET', 'POST'])
def relatorio():
    if request.method == 'POST':
       
        dados = request.json
      
        data_inicial = dados.get('data_inicial', '')
        data_final = dados.get('data_final', '')
        filtro_data = dados.get('filtro_data', '')
        filial = dados.get('filial', '')
        email = dados.get('email', '')
        empresa = dados.get('empresa', '')
        plataforma = dados.get('plataforma', '')
        titulo = dados.get('titulo', '')
       
        chamados_ref = db.collection('chamados')
        
        query = chamados_ref
       
        if data_inicial and data_final:
            query = query.where('data_criacao', '>=', data_inicial).where('data_criacao', '<=', data_final)
        
        if filtro_data:
            
            if filtro_data == 'fechamento':
                query = query.where('data_fechamento', '!=', None)  
            else:
                query = query.where('data_abertura', '!=', None)  

        if filial:
            query = query.where('filial', '==', filial)

        if email:
            query = query.where('email', '==', email)

        if empresa:
            query = query.where('empresa', '==', empresa)

        if plataforma:
            query = query.where('plataforma', '==', plataforma)

        if titulo:
            query = query.where('titulo', '==', titulo)

        
        resultados = query.stream()

       
        chamados = []
        for doc in resultados:
            chamado = doc.to_dict()
            chamado['id_chamado'] = doc.id  
            chamados.append(chamado)

       
        return jsonify({"chamados": chamados})

    
    return render_template('tela_relatorio.html')
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000)) # Utiliza a porta do render para deploy
    app.run(host="0.0.0.0", port=port, debug=True)

 
