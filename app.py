from flask import Flask, request, render_template, flash, redirect, url_for, jsonify, Response, get_flashed_messages, session
from flask_session import Session
from datetime import datetime, timedelta
import pytz
from rotas import create_work_item, consultar_chamado
import os
from deep_translator import GoogleTranslator
from rotas import consultar_comentarios, adicionar_comentario_card
from werkzeug.security import generate_password_hash, check_password_hash
#from supabase_config import supabase
from supabase import create_client, Client
from functools import wraps
import random
import json
import string
from flask_socketio import SocketIO, emit
from atendimentos import get_chamado_detalhes, get_usuario_by_email, update_chamado, get_chamados_abertos, add_comentario,get_comentarios_by_chamado_id
#from supabase_config import SUPABASE_URL, SUPABASE_KEY
from werkzeug.utils import secure_filename
import uuid
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To
from dotenv import load_dotenv
import logging
import secrets
from movimentacoes import registrar_movimentacao_chamado

load_dotenv()
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app_logger = logging.getLogger(__name__)

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY")

SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'https://braveo.vercel.app') #alterar em prd
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME')

# Configuração de sessão
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=2)  # tempo da seção
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'myapp:'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
app.config['SESSION_FILE_THRESHOLD'] = 500
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True  # True em produção com HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
Session(app)

SITE_BASE_URL = os.getenv('SITE_BASE_URL', 'https://braveo.vercel.app') # alterar em prd
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_FROM_NAME = os.getenv('EMAIL_FROM_NAME')

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

SP_TZ = pytz.timezone('America/Sao_Paulo')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'mov', 'avi', 'wmv', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}


def obter_usuario_por_is(usuario_id):
    try:
        response = supabase.table('usuarios').select('*').eq('id', usuario_id).single().execute()
        return response.data
    except Exception as e:
        app_logger.error(f"Erro ao buscar usuario{usuario_id}: {e}")
        return None 

def obter_usuario_por_email_tel(identifier):
    try:
        response = supabase.table('usuarios').select('*').eq('email', identifier).execute()
        if response.data:
            if len(response.data) > 1:
                app_logger.warning(f"Múltiplos usuários encontrados para o email {identifier}. Retornando o primeiro.")
            return response.data[0] 
    except Exception:
        pass

    try:
        clean_phone = ''.join(filter(str.isdigit, identifier))
        response = supabase.table('usuarios').select('*').eq('telefone', clean_phone).execute()
        if response.data:
            if len(response.data) > 1:
                app_logger.warning(f"Múltiplos usuários encontrados para o telefone {clean_phone}. Retornando o primeiro.")
            return response.data[0]
    except Exception as e:
        app_logger.error(f"Erro ao buscar usuário por email/telefone no Supabase: {e}", exc_info=True)
        pass

    return None
def gerar_token_recuperacao():
    return secrets.token_urlsafe(48)

def salvar_token_recuperacao(user_id, token):
    try:
        expires_at = datetime.now(pytz.utc) + timedelta(hours=1)
        expires_at_iso = expires_at.isoformat(timespec='seconds').replace('+00:00', 'Z')
        supabase.table('password_reset_tokens').delete().eq('user_id', user_id).execute()

        response = supabase.table('password_reset_tokens').insert({
            'user_id': user_id,
            'token': token,
            'expires_at': expires_at_iso,
            'created_at': datetime.now(pytz.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        }).execute()
        return response.data is not None
    except Exception as e:
        app_logger.error(f"Erro ao salvar token de recuperação para user {user_id}: {e}", exc_info=True)
        return False

def verificar_token_recuperacao(token):
    try:
        response = supabase.table('password_reset_tokens').select('user_id, expires_at').eq('token', token).single().execute()
        token_data = response.data

        if token_data:
            expires_at_str = token_data.get('expires_at')
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                
                if expires_at.tzinfo is None:
                    expires_at = pytz.utc.localize(expires_at)
                
                if datetime.now(pytz.utc) < expires_at:                   
                    supabase.table('password_reset_tokens').delete().eq('token', token).execute()
                    return token_data['user_id']
                else:
                    app_logger.warning(f"Token de recuperação expirado: {token}")
                    supabase.table('password_reset_tokens').delete().eq('token', token).execute()
        else:
            app_logger.warning(f"Token de recuperação não encontrado: {token}")

    except Exception as e:
        app_logger.error(f"Erro ao verificar token de recuperação {token}: {e}", exc_info=True)
    return None

def atualizar_senha_usuario(usuario_id, new_password):
    try:
        hashed_password = generate_password_hash(new_password)
        response = supabase.table('usuarios').update({'senha': hashed_password}).eq('id', usuario_id).execute()
        
        if response.data:
            return True
        else:
            app_logger.error(f"Supabase retornou vazio ao atualizar senha para user {usuario_id}. Erro: {response.error}")
            return False
    except Exception as e:
        app_logger.error(f"Erro fatal ao atualizar senha para user {usuario_id}: {e}", exc_info=True)
        return False
    
def enviar_email(to_email, subject, body_html):
    if not SENDGRID_API_KEY:
        app_logger.error("SENDGRID_API_KEY não configurada no .env. Email não enviado.")
        return False
    if not EMAIL_FROM:
        app_logger.error("EMAIL_FROM não configurado no .env. Email não enviado.")
        return False
    
    from_email_obj = Email(EMAIL_FROM, EMAIL_FROM_NAME or EMAIL_FROM)
    to_email_obj = To(to_email)

    message = Mail(
        from_email=from_email_obj,
        to_emails=to_email_obj,
        subject=subject,
        html_content=body_html
    )
    
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)        

        if 200 <= response.status_code < 300:
            app_logger.info(f"Email enviado com sucesso para {to_email} via SendGrid. Status: {response.status_code}")
            return True
        else:
            app_logger.error(f"Falha ao enviar email para {to_email} via SendGrid. Status: {response.status_code}, Body: {response.body}, Headers: {response.headers}")
            return False
    except Exception as e:
        app_logger.error(f"Erro ao enviar email para {to_email} com SendGrid: {e}", exc_info=True)
        return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/upload_images', methods=['POST'])
def upload_images():
    if 'images' not in request.files:
        return jsonify({'error': 'Nenhum arquivo na requisição'}), 400

    uploaded_files = request.files.getlist('images')
    if not uploaded_files:
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400

    anexo_urls = []
    bucket_name = "chamadoanexos" 
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)           
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}_{original_filename}"
            
            try:                
                file_content = file.read()
                print(f"DEBUG: Tipo de file_content: {type(file_content)}")               
                response_upload = supabase.storage.from_(bucket_name).upload(
                    unique_filename,
                    file_content,
                    {'content-type': file.content_type} 
                )                             
                if hasattr(response_upload, 'path') and response_upload.path:                  
                    public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{unique_filename}"
                    anexo_urls.append({
                        "url": public_url,
                        "filename": original_filename,
                        "mimetype": file.content_type 
                    })
                else:                   
                    print(f"Supabase upload returned unexpected data for {original_filename}: {response_upload}")
                    return jsonify({'error': f'Falha inesperada ao fazer upload para o Supabase para {original_filename}'}), 500
            except Exception as e:               
                print(f"Erro ao processar upload do arquivo {original_filename}: {e}")               
                if hasattr(e, 'message'): 
                    return jsonify({'error': f'Erro ao fazer upload para o Supabase: {e.message}'}), 500
                elif hasattr(e, 'response') and hasattr(e.response, 'json'): 
                    try:
                        error_json = e.response.json()
                        return jsonify({'error': f'Erro ao fazer upload para o Supabase: {error_json.get("error", "Erro desconhecido")}'}), 500
                    except:
                        pass 
                return jsonify({'error': f'Erro interno ao processar o arquivo: {str(e)}'}), 500
        else:
            return jsonify({'error': f'Tipo de arquivo não permitido ou arquivo inválido: {file.filename}'}), 400

    return jsonify({'image_urls': anexo_urls}), 200

def get_user_name_by_id(email):
    try:
        response = supabase.table('usuarios').select('nome').eq('email', email).execute()
        if response.data:
            return response.data[0]['nome']
        return "Usuario Desconhecido"
    except Exception as e:
        print(f"❌ Erro ao obter o nome do usuário: {str(e)}")
        return "Usuario Desconhecido"


def gerar_id_chamado():
    digitos = ''.join(random.choices(string.digits, k=3))
    letras = ''.join(random.choices(string.ascii_uppercase, k=3))
    id_chamado = f"{digitos}-{letras}"

    try:
        response = supabase.table('chamados').select('id_chamado').eq('id_chamado', id_chamado).execute()
        if response.data and len(response.data) > 0:
            return gerar_id_chamado()
        return id_chamado
    except Exception as e:
        print(f"❌ Erro ao gerar o ID do chamado: {str(e)}")
        return f"{random.randint(100, 999)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}{random.choice(string.ascii_uppercase)}"

def salvar_chamado_supabase(titulo, descricao, email, empresa, plataforma, filial, usuario_id, categoria, responsavel, anexos=None):
    try:   
      
        if anexos is None:
            anexos = []

        id_chamado = gerar_id_chamado() 
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        agora = datetime.now(fuso_horario)

        categoria_formatada = categoria.capitalize() if categoria else ''
        prioridade_original = 'Baixa'
        
        prioridade_formatada = prioridade_original[0].lower() + prioridade_original[1:] if prioridade_original else 'baixa'

        dados_chamado = {
            'id_chamado': id_chamado,
            'titulo': titulo,
            'descricao': descricao,
            'email_solicitante': email,
            'empresa_chamado': empresa,
            'plataforma_chamado': plataforma,
            'filial_chamado': filial,
            'usuario_id': usuario_id,
            'categoria': categoria_formatada,
            'status_chamado': 'Aberto',
            'data_criacao': agora.strftime('%Y-%m-%dT%H:%M:%S'),
            'data_atualizacao': agora.isoformat(),
            'prioridade': prioridade_formatada,
            'responsavel_atendimento': responsavel,
            'anexos': anexos 
        }

        print(f"Inserindo chamado no banco: {dados_chamado}")
        response = supabase.table('chamados').insert(dados_chamado).execute()
        print(f"Retorno SUPA: {response}")
            

        if response.data and len(response.data) > 0:           
            mov_registrada = registrar_movimentacao_chamado(
                id_chamado=id_chamado,
                tipo='Criação de Chamado',
                valor_anterior='N/A',
                valor_novo='Aberto',
                usuario=responsavel 
            )
            if not mov_registrada:
                print(f"ATENÇÃO: Chamado {id_chamado} criado, mas falha ao registrar movimentação de criação.")

            return {
                'success': True,
                'id_chamado': id_chamado,
                'message': f'Chamado criado com sucesso! ID: {id_chamado}',
                'data': response.data[0]
            }
        else:            
            error_message = response.error.message if response.error else "Erro desconhecido ao criar o chamado."
            print(f"Erro ao criar o chamado no Supabase: {error_message}")
            return {
                'success': False,
                'error': f'Erro ao criar o chamado: {error_message}',
            }
    except Exception as e:
        print(f"❌ Erro ao salvar o chamado: {str(e)}")
        return {
            'success': False,
            'error': f'Erro ao criar o chamado: {str(e)}'
        }
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_logado' not in session or not session.get('usuario_logado'):
            flash('Faça login para acessar essa página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        

        response = supabase.table('usuarios').select('*').eq('email', email).execute()
        dados = response.data

        if not dados:
            flash('E-mail ou senha incorretos', 'error')
            return redirect(url_for('login'))

        usuario = dados[0]
        senha_hash = usuario['senha']

        if check_password_hash(senha_hash, senha):
            session.permanent = True
            session['usuario_logado'] = True
            session['email'] = email
            session['usuario_id'] = usuario['id']
            session['nome'] = usuario['nome']
            session['empresa'] = usuario['empresa']
            session['funcao'] = usuario['funcao']
            session['login_time'] = datetime.now(SP_TZ).isoformat()
            session['acesso'] = usuario['acesso']

            supabase.table('log_acessos').insert({
                'usuario_id': usuario['id'],
                'data_login': session['login_time']
            }).execute()

            return redirect(url_for('menu_modulo'))
        else:
            flash('E-mail ou senha incorretos', 'error')
            return redirect(url_for('login'))

    if 'usuario_logado' in session and session.get('usuario_logado'):
        return redirect(url_for('menu_modulo'))

    return render_template('tela_login.html')

@app.route('/logout')
@login_required
def logout():
    usuario_id = session.get('usuario_id')
    data_login = session.get('login_time')

    if usuario_id and data_login:
        response = supabase.table('log_acessos') \
            .select('id') \
            .eq('usuario_id', usuario_id) \
            .eq('data_login', data_login) \
            .execute()

        if response.data:
            log_id = response.data[0]['id']
            data_logout = datetime.now(SP_TZ).isoformat()
            supabase.table('log_acessos') \
                .update({'data_logout': data_logout}) \
                .eq('id', log_id) \
                .execute()

    session.clear()
    flash('Logout realizado com sucesso', 'success')
    return redirect(url_for('login'))

# --- Rotas de Páginas (Renderizam HTML) ---
@app.route('/')
def index():
    if session.get('usuario_logado') and session.get('usuario_id'):
        return redirect(url_for('menu_modulo'))
    return redirect(url_for('login'))

@app.route('/menu')
@login_required
def menu_modulo():
    print(f"Sessão atual: {dict(session)}")
    print(f"Sessão permanente: {session.permanent}")
    return render_template('menu_modulo.html')

@app.route("/aberturaChamado", methods=["GET", "POST"])
@login_required
def abertura():
    if request.method == "POST":
        try:
            empresa = request.form.get("empresa")
            plataforma = request.form.get("plataforma")
            email = request.form.get("email")
            titulo = request.form.get("titulo2")
            descricao = request.form.get("descricao")
            filial = request.form.get("filial")
            categoria = request.form.get("categoria")
            usuario_id = session.get('usuario_id')

            campos_obrigatorios = []
            if not titulo or titulo.strip() == "": campos_obrigatorios.append("Título")
            if not descricao or descricao.strip() == "": campos_obrigatorios.append("Descrição")
            if not email or email.strip() == "": campos_obrigatorios.append("E-mail")
            if not empresa or empresa.strip() == "": campos_obrigatorios.append("Empresa")
            if not plataforma or plataforma.strip() == "": campos_obrigatorios.append("Plataforma")

            if campos_obrigatorios:
                campos_faltando = ", ".join(campos_obrigatorios)
                flash(f"Os seguintes campos são obrigatórios: {campos_faltando}", "error")
                if request.is_json or request.headers.get('Content-Type') == 'application/json':
                    return jsonify({"flash_messages": get_flashed_messages(with_categories=True)})
                return redirect(url_for("abertura"))

            import re
            email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
            if not re.match(email_regex, email.strip()):
                flash("Por favor, insira um e-mail válido.", "error")
                if request.is_json or request.headers.get('Content-Type') == 'application/json':
                    return jsonify({"flash_messages": get_flashed_messages(with_categories=True)})
                return redirect(url_for("abertura"))
            

            anexos = []
            if 'evidencia' in request.files:
                evidencia_files = request.files.getlist('evidencia')
                for file in evidencia_files:
                    if file.filename != '':
                        original_filename = secure_filename(file.filename)
                        timestamp = int(datetime.now().timestamp() * 1000)
                        unique_filename = f"{timestamp}-{original_filename}"
                        bucket_name = "chamadoanexos"

                        try:
                            file_content = file.read()

                            supabase.storage.from_(bucket_name).upload(
                                unique_filename,
                                file_content,
                                {"content-type": file.content_type}
                            )

                            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{unique_filename}"
                            anexos.append({
                                "url": public_url,
                                "filename": original_filename,
                                "mimetype": file.content_type
                            })

                            print(f"✅ Anexo enviado: {public_url}")

                        except Exception as e:
                            print(f"❌ Erro ao subir anexo {original_filename}: {e}")
                            flash(f"Erro ao fazer upload do anexo {original_filename}.", "error")
            resultado = salvar_chamado_supabase(
                titulo=titulo.strip(),
                descricao=descricao.strip(),
                email=email.strip(),
                empresa=empresa.strip(),
                plataforma=plataforma.strip(),
                categoria=categoria.strip() if categoria else None,
                filial=filial.strip() if filial else None,
                usuario_id=usuario_id,
                responsavel=session.get('nome','Usuário Desconhecido'),
                anexos=anexos	
            )

            if resultado['success']:
                flash(f"Chamado criado com sucesso! ID: {resultado['id_chamado']}", "success")
                emit_dashboard_data()
                try:
                    enviar_email(email, resultado['id_chamado'])
                except Exception as e:
                    print(f"Erro ao enviar email: {e}")
            else:
                flash(resultado['error'], "error")

            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"flash_messages": get_flashed_messages(with_categories=True)})
            return redirect(url_for("abertura"))

        except Exception as e:
            flash(f"Erro interno do servidor: {str(e)}", "error")
            if request.is_json or request.headers.get('Content-Type') == 'application/json':
                return jsonify({"flash_messages": get_flashed_messages(with_categories=True)})
            return redirect(url_for("abertura"))
    return render_template("menu_modulo.html")


@app.route('/registrar_chamado', methods=['GET', 'POST'])
@login_required
def registrar_chamado():
    if request.method == 'POST':
        try:
            titulo = request.form['titulo']
            email_solicitante = request.form['email_solicitante']
            empresa_chamado = request.form['empresa_chamado']
            plataforma_chamado = request.form['plataforma_chamado']
            filial_chamado = request.form['filial_chamado']
            categoria = request.form['categoria']
            prioridade = request.form['prioridade']
            descricao = request.form['descricao']
            responsavel = session.get('nome', 'Não atribuído')

            data_criacao_sp = datetime.now(SP_TZ)
            data_criacao_iso = data_criacao_sp.isoformat()

            new_chamado_data = {
                "titulo": titulo,
                "email_solicitante": email_solicitante,
                "empresa_chamado": empresa_chamado,
                "plataforma_chamado": plataforma_chamado,
                "filial_chamado": filial_chamado,
                "status_chamado": "Aberto",
                "data_criacao": data_criacao_iso,
                "prioridade": prioridade,
                "categoria": categoria,
                "descricao": descricao,
                "responsavel": responsavel 
            }

            response = supabase.table('chamados').insert(new_chamado_data).execute()

            if response.data:
                flash('Chamado registrado com sucesso!', 'success')
                socketio.emit('novo_chamado_criado', {
                    'id': response.data[0]['id_chamado'],
                    'titulo': response.data[0]['titulo']
                })
               
                return redirect(url_for('index'))
            else:
                flash('Erro ao registrar o chamado no banco de dados.', 'danger')

        except Exception as e:
            flash(f'Erro ao registrar chamado: {e}', 'danger')

    return render_template('registrar_chamado.html')

@app.route('/detalhes_chamados')
@login_required
def detalhes_chamados():
    chamados = get_chamados_abertos()
    nome_usuario_logado = session.get('nome', 'Usuário Desconhecido')

    for chamado in chamados:
        usuario = get_usuario_by_email(chamado.get('email_solicitante', ''))
        chamado['usuario_nome'] = usuario.get('nome', 'Desconhecido')
        chamado['telefone'] = usuario.get('telefone', '')        
        #chamado['data_criacao'] = chamado.get('data_criacao', '')

    return render_template(
        'detalhes_chamados.html',
        chamados=chamados,
        supabase_url=SUPABASE_URL,
        supabase_anon_key=SUPABASE_KEY,
        usuario_logado_nome=nome_usuario_logado
    )
@app.route('/consultar_chamado')
@login_required
def consultar_chamado_page():
    return render_template('consultar_chamado.html', usuario_nome_logado=session.get('nome'))

@app.route("/consultar_chamado_supabase", methods=["POST"])
def consultar_chamado_supabase():
    try:
        data = request.get_json()
        id_chamado = data.get("id_chamado")

        if not id_chamado:
            return jsonify({"error": "ID do chamado é obrigatório."})

        response = supabase.table('chamados').select('*').eq('id_chamado', id_chamado).execute()

        if response.data and len(response.data) > 0:
            chamado = response.data[0]
            return jsonify({
                "id_chamado": chamado['id_chamado'],
                "titulo": chamado['titulo'],
                "descricao": chamado['descricao'],
                "status": chamado['status_chamado'],
                "empresa": chamado['empresa_chamado'],
                "plataforma": chamado['plataforma_chamado'],
                "data_criacao": chamado['data_criacao'],
                "email_solicitante": chamado['email_solicitante'],
                "categoria": chamado['categoria']
            })
        else:
            return jsonify({"error": f"Chamado {id_chamado} não encontrado."})

    except Exception as e:
        print(f"Erro ao consultar chamado: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}"})

@app.route('/api/chamados-abertos')
@login_required
def api_chamados_abertos():
    chamados = get_chamados_abertos()
    for chamado in chamados:
        usuario = get_usuario_by_email(chamado.get('email_solicitante', ''))
        chamado['usuario_nome'] = usuario.get('nome', 'Desconhecido')
        chamado['telefone'] = usuario.get('telefone', '')
        chamado['email'] = usuario.get('email_solicitante', '')

        data_criacao = chamado.get('data_criacao')

        if isinstance(data_criacao, datetime):            
            data_brasilia = data_criacao + timedelta(hours=3)
            chamado['data_criacao'] = data_brasilia.strftime('%Y-%m-%dT%H:%M:%S')
        elif isinstance(data_criacao, str):
            try:                
                dt = datetime.fromisoformat(data_criacao)
                dt_brasilia = dt + timedelta(hours=3)
                chamado['data_criacao'] = dt_brasilia.strftime('%Y-%m-%dT%H:%M:%S')
            except Exception as e:
                print(f"Data inválida: {data_criacao} - {e}")
                chamado['data_criacao'] = data_criacao
        else:
            chamado['data_criacao'] = None

    return jsonify(chamados)
@app.route('/api/detalhes_chamado/<id_chamado>')
@login_required
def api_detalhes_chamado(id_chamado):
    chamado = get_chamado_detalhes(id_chamado)
    if chamado:
        usuario = get_usuario_by_email(chamado.get('email_solicitante', ''))
        chamado['usuario_nome'] = usuario.get('nome', 'Desconhecido')
        chamado['telefone'] = usuario.get('telefone', '')
        chamado['chamado_id'] = id_chamado
        return jsonify(chamado)
    else:
        return jsonify({'error': 'Chamado not found'}), 404


@app.route('/api/atualizar_chamado/<string:id_chamado>', methods=['PUT'])
@login_required
def atualizar_chamado(id_chamado):
    try:
        dados = request.get_json()

        if not id_chamado:
            return jsonify({'success': False, 'error': 'ID do chamado é obrigatório'}), 400

        # Buscar dados atuais do chamado para comparação
        chamado_atual = supabase.table('chamados').select('*').eq('id_chamado', id_chamado).single().execute()
        if not chamado_atual.data:
            return jsonify({'success': False, 'error': 'Chamado não encontrado'}), 404

        dados_atuais = chamado_atual.data
        usuario_logado = session.get('nome', 'Sistema')

        campos_atualizacao = {}
        if 'empresa_chamado' in dados: campos_atualizacao['empresa_chamado'] = dados['empresa_chamado']
        if 'plataforma_chamado' in dados: campos_atualizacao['plataforma_chamado'] = dados['plataforma_chamado']
        if 'filial_chamado' in dados: campos_atualizacao['filial_chamado'] = dados['filial_chamado']
        if 'categoria' in dados: campos_atualizacao['categoria'] = dados['categoria']
        if 'status_chamado' in dados: campos_atualizacao['status_chamado'] = dados['status_chamado']
        if 'prioridade' in dados: campos_atualizacao['prioridade'] = dados['prioridade']
        if 'responsavel_atendimento' in dados: campos_atualizacao['responsavel_atendimento'] = dados['responsavel_atendimento']
        if 'comentario_novo' in dados: campos_atualizacao['comentario_novo'] = dados['comentario_novo']  # Adicionado campo comentario_novo

        if not campos_atualizacao:
            return jsonify({'success': False, 'error': 'Nenhum campo para atualizar fornecido'}), 400

        sucesso = update_chamado(id_chamado, campos_atualizacao)

        if sucesso:
            # Registrar movimentações para mudanças de status e responsável
            if 'status_chamado' in campos_atualizacao and dados_atuais['status_chamado'] != campos_atualizacao['status_chamado']:
                
                if 'status_chamado' in campos_atualizacao and dados_atuais['status_chamado'] != campos_atualizacao['status_chamado']:
                    registrar_movimentacao_chamado(
                        id_chamado, 
                        'status alterado para', 
                        dados_atuais['status_chamado'], 
                        campos_atualizacao['status_chamado'], 
                        usuario_logado
                    )

            if 'responsavel_atendimento' in campos_atualizacao and dados_atuais.get('responsavel_atendimento') != campos_atualizacao['responsavel_atendimento']:
                registrar_movimentacao_chamado(
                    id_chamado, 
                    'responsável alterado para', 
                    dados_atuais.get('responsavel_atendimento', 'Não definido'), 
                    campos_atualizacao['responsavel_atendimento'], 
                    usuario_logado
                )
                socketio.emit('chamado_atualizado', {
                    'id': id_chamado,
                    'status': campos_atualizacao.get('status_chamado', ''),
                    'responsavel': campos_atualizacao.get('responsavel_atendimento', ''),
                })
            # Emitir eventos WebSocket para notificar sobre a atualização
            socketio.emit('chamado_atualizado', {'id': id_chamado, 'status': campos_atualizacao.get('status_chamado')})
            socketio.emit('atualizacao_chamado')  # Para atualizar o dashboard
            return jsonify({'success': True, 'message': 'Chamado atualizado com sucesso'}), 200
        else:
            return jsonify({'success': False, 'error': 'Falha ao atualizar o chamado no banco de dados'}), 500

    except Exception as e:
        print(f"Erro ao atualizar chamado: {str(e)}")
        return jsonify({'success': False, 'error': f'Erro interno ao processar atualização: {str(e)}'}), 500

@app.route("/aberturaChamadoAzure", methods=["GET", "POST"])
@login_required
def abertura_azure():

    if request.method == "POST":
        empresa = request.form.get("empresa")
        plataforma = request.form.get("plataforma")
        email = request.form.get("email")
        titulo = request.form.get("titulo2")
        descricao = request.form.get("descricao")
        evidencia_files = request.files.getlist('evidencia')
        filial = request.form.get("filial")

        if not email or not titulo or not descricao:
            flash("E-mail, título e descrição são obrigatórios.", "error")
            return jsonify({"flash_messages": get_flashed_messages(with_categories=True)})

        result = create_work_item(titulo, descricao, empresa, plataforma, email, filial, evidencia_files=evidencia_files)

        if isinstance(result, dict) and "error" in result:
            flash(result["error"], "error")
            return jsonify({"flash_messages": get_flashed_messages(with_categories=True)})
        else:
            flash(f"Chamado criado com sucesso! ID: {result.get('id')}", "success")
            if result:
                id_chamado = result.get("id")
                enviar_email(email, id_chamado)
                return jsonify({"flash_messages": get_flashed_messages(with_categories=True)})
        return redirect(url_for("abertura_azure", titulo=titulo, descricao=descricao, email=email))
    return render_template("index.html")

@app.route("/consultar", methods=["POST"])
@login_required
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
        return jsonify(dados)

@app.route("/consultar_comentarios_azure", methods=["GET"])
@login_required
def consultar_comentarios_route():
    id_chamado = request.args.get("id_chamado")
    plataforma = request.args.get("plataforma")

    if not id_chamado or not plataforma:
        return jsonify({"error": "ID do chamado e plataforma são obrigatórios."})

    resultado = consultar_comentarios(id_chamado, plataforma="click")

    if isinstance(resultado, Response):
        resultado = resultado.json

    if isinstance(resultado, list):
        return jsonify({"comentarios": resultado})

    if isinstance(resultado, dict) and "error" in resultado:
        return jsonify({"error": resultado["error"]})
    else:
        return jsonify({"comentarios": resultado.get("comentarios", [])})

@app.route("/adicionar_comentario_azure", methods=["POST"])
@login_required
def adicionar_comentario():
    data = request.get_json()
    id_chamado = data.get("id_chamado")
    comentario = data.get("comentario")
    plataforma = data.get("plataforma")

    if not id_chamado or not comentario:
        return jsonify({"error": "ID do chamado e comentário são obrigatórios."})

    if not plataforma:
        chamado_info = consultar_chamado(id_chamado, plataforma="click")
        if "error" in chamado_info:
            return jsonify({"error": f"Não foi possível determinar a plataforma do chamado {id_chamado}."})
        plataforma = chamado_info.get("plataforma")
    if not isinstance(plataforma, str):
            return jsonify({"error": "Plataforma inválida"})

    resultado = adicionar_comentario_card(id_chamado, comentario, plataforma)
    return jsonify(resultado)
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'GET':
        return render_template("tela_cadastro.html")

    if request.method == 'POST':
        try:
            data = request.get_json()

            nome = data.get('nome')
            telefone = data.get('telefone')
            empresa = data.get('empresa')
            funcao = data.get('funcao')
            email = data.get('email')
            senha = data.get('senha')

            if not all([nome, telefone, empresa, funcao, email, senha]):
                return jsonify({"error": "Todos os campos são obrigatórios."}), 400

            response = supabase.table('usuarios').select('email').eq('email', email).execute()
            if response.data and len(response.data) > 0:
                return jsonify({"error": "E-mail já cadastrado."}), 400

            senha_hash = generate_password_hash(senha)

            insert_response = supabase.table('usuarios').insert({
                'nome': nome,
                'telefone': telefone,
                'empresa': empresa,
                'funcao': funcao,
                'email': email,
                'senha': senha_hash,
                'acesso': 'ku'
            }).execute()

            if not insert_response.data:
                return jsonify({"error": "Erro ao cadastrar usuário."}), 500

            return jsonify({"message": "Cadastro realizado com sucesso!"}), 200

        except Exception as e:
            print("Erro no cadastro:", e)
            return jsonify({"error": "Erro na comunicação com o servidor."}), 500

@app.route('/tela_login')
def tela_login():
    if session.get('usuario_logado') and session.get('usuario_id'):
        return redirect(url_for('menu_modulo'))
    return render_template('tela_login.html')

# (REMOVER EM PRODUÇÃO)
@app.route('/debug_session')
def debug_session():
    return jsonify({
        'session_data': dict(session),
        'session_permanent': session.permanent,
        'session_id': request.cookies.get('session'),
        'cookies': dict(request.cookies)
    })

@app.before_request
def check_session():
    public_routes = ['login', 'tela_login', 'cadastro', 'static', 'abertura','solicitar_recuperacao_senha',
    'processar_recuperacao_senha',
    'redefinir_senha_confirmar']
    if request.endpoint in public_routes:
        return

    if request.endpoint and not session.get('usuario_logado'):
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({"error": "Sessão expirada. Faça login novamente."}), 401
        return redirect(url_for('login'))

@app.context_processor
def inject_user():
    if session.get('usuario_logado'):
        return {
            'usuario_logado': session.get('usuario_logado'),
            'usuario_nome': session.get('nome'),
            'usuario_email': session.get('email'),
            'usuario_empresa': session.get('empresa')
        }
    return {}
@app.route('/api/chamados/<string:id_chamado>/comentarios', methods=['POST'])
@login_required
def handle_adicionar_comentario(id_chamado):
    try:
        dados = request.get_json()
        comentario_texto = dados.get('comentario_texto')
        anexos = dados.get('anexos', [])

        if not comentario_texto:
            return jsonify({"error": "Comentario vazio"}), 400
        
        nome_usuario = session.get('nome')
        email_usuario = session.get('email')

        if not nome_usuario or not email_usuario:
            return jsonify({"error": "Usuário nao encontrado"}), 400

        novo_comentario = add_comentario(id_chamado, nome_usuario, email_usuario, comentario_texto, anexos)

        if novo_comentario:
            if 'socketio' in globals():
                socketio.emit('novo_comentario', {'id_chamado': id_chamado, 'comentario': novo_comentario})
                emit_dashboard_data()
            return jsonify(novo_comentario), 200
        else:
            return jsonify({"error": "Erro ao adicionar comentario ao chamado"}), 500
    except Exception as e:
        print(f"Erro ao adicionar comentario ao chamado {id_chamado}: {e}")
        return jsonify({"error": "Erro ao adicionar comentario ao chamado"}), 500
    
@app.route('/api/chamados/<string:id_chamado>/comentarios', methods=['GET'])
@login_required
def get_comentarios_chamado(id_chamado):
    try:
        comentarios = get_comentarios_by_chamado_id(id_chamado)
        for c in comentarios:
            if isinstance(c.get('data_hora'), datetime):
                c['data_hora'] = c['data_hora'].strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(comentarios), 200
    except Exception as e:
        print(f"Erro ao buscar comentários para o chamado {id_chamado}: {e}")
        return jsonify({"error": "Erro ao buscar comentários para o chamado"}), 500
@app.route('/api/chamados/<string:id_chamado>/adicionar_comentario', methods=['POST'])
@login_required
def adicionar_comentario_api(id_chamado):
    try:
        data = request.json
        comentario_texto = data.get('comentario')
        anexos = data.get('anexos', [])

        if not comentario_texto and not anexos:
            return jsonify({"error": "Comentarios vazio"}), 400
        nome_usuario = session.get('nome')
        email_usuario = session.get('email')

        if not nome_usuario or not email_usuario:
            return jsonify({"error": "Usuário nao encontrado"}), 400

        novo_comentario = add_comentario(id_chamado, nome_usuario, email_usuario, comentario_texto, anexos)

        if novo_comentario:
            socketio.emit('novo_comentario', {'id_chamado': id_chamado})
            if isinstance(novo_comentario.get('data_hora'), datetime):
                novo_comentario['data_hora'] = novo_comentario['data_hora'].strftime('%Y-%m-%d %H:%M:%S')
            return jsonify(novo_comentario), 200
        else:
            return jsonify({"error": "Erro ao adicionar comentario ao chamado"}), 500
    except Exception as e:
        print(f"Erro ao adicionar comentario ao chamado {id_chamado}: {e}")
        return jsonify({"error": "Erro ao adicionar comentario ao chamado"}), 500
    
@app.route('/api/chamados/<string:id_chamado>', methods=['GET'])
@login_required
def get_chamado_detalis_api(id_chamado):
    try:
        chamado_detalhes = get_chamado_detalhes(id_chamado)
        if chamado_detalhes:
            
            if 'data_abertura' in chamado_detalhes and isinstance(chamado_detalhes['data_abertura'], datetime):
                chamado_detalhes['data_abertura'] = chamado_detalhes['data_abertura'].strftime('%Y-%m-%d %H:%M:%S')
            if 'data_conclusao' in chamado_detalhes and isinstance(chamado_detalhes['data_conclusao'], datetime):
                chamado_detalhes['data_conclusao'] = chamado_detalhes['data_conclusao'].strftime('%Y-%m-%d %H:%M:%S')
            if 'id_chamado_azure' not in chamado_detalhes:
                chamado_detalhes['id_chamado_azure'] = None           
           
            if 'anexos' not in chamado_detalhes or chamado_detalhes['anexos'] is None:
                chamado_detalhes['anexos'] = []
            return jsonify(chamado_detalhes), 200
        else:
            return jsonify({"error": "Chamado nao encontrado"}), 404
    except Exception as e:    
        print(f"Erro ao buscar detalhes do chamado {id_chamado}: {e}")
        return jsonify({"error": "Erro ao buscar detalhes do chamado"}), 500
@app.route('/api/meus-chamados', methods=['GET'])
@login_required
def meus_chamados():
    try:
        user_email = session.get('email')
        if not user_email:
            return jsonify({"error": "Usuário não logado"}), 401

        todos_chamados = supabase.table('chamados').select('*').execute().data or []
        chamados_filtrados = [
            c for c in todos_chamados 
            if str(c.get('email_solicitante')).lower() == str(user_email).lower()
        ]

        formatted_chamados = []
        for chamado in chamados_filtrados:
            data_criacao = chamado.get('data_criacao')
            if isinstance(data_criacao, datetime):
                data_criacao = data_criacao.isoformat()

            formatted_chamados.append({
                'id_chamado': chamado.get('id_chamado'),
                'titulo': chamado.get('titulo'),
                'status_chamado': chamado.get('status_chamado'),
                'prioridade': chamado.get('prioridade'),
                'data_criacao': data_criacao,
                'email_solicitante': chamado.get('email_solicitante'),
                'empresa_chamado': chamado.get('empresa_chamado'),
                'plataforma_chamado': chamado.get('plataforma_chamado'),
                'descricao': chamado.get('descricao'),
                'anexos': chamado.get('anexos'),
            })

        return jsonify(formatted_chamados)

    except Exception as e:
        print(f"Erro ao carregar chamados do usuário: {e}")
        return jsonify({"error": "Erro ao carregar chamados."}), 500

@app.route('/api/chamados/<id_chamado>/comentarios')
@login_required
def comentarios_chamado(id_chamado):
    try:
        response = supabase.table('comentarios_chamados') \
            .select('comentario, data_hora, nome_usuario, anexos') \
            .eq('id_chamado', id_chamado) \
            .order('data_hora', desc=False) \
            .execute()

        if response.data:
            comentarios = response.data
            for c in comentarios:
                if isinstance(c['data_hora'], str):        
                    try:
                        dt = datetime.fromisoformat(c['data_hora'].replace('Z', '+00:00'))
                    except ValueError:                        
                        dt = datetime.strptime(c['data_hora'], '%Y-%m-%dT%H:%M:%S.%f')
                else:
                    dt = c['data_hora']                  
                sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
                dt_local = dt.astimezone(sao_paulo_tz)
                c['data_hora_formatada'] = dt_local.strftime('%d/%m/%Y %H:%M:%S')
                anexos_raw = c.get('anexos')
                if isinstance(anexos_raw, str):
                    try:
                        c['anexos'] = json.loads(anexos_raw)
                    except json.JSONDecodeError:            
                        c['anexos'] = []
                elif anexos_raw is None:
                    c['anexos'] = []
                elif not isinstance(anexos_raw, list):
                    c['anexos'] = []              
               

            return jsonify(comentarios)
        else:
            return jsonify([])
    except Exception as e:
        print(f"Erro ao buscar comentários para o chamado {id_chamado}: {e}")
        return jsonify({"error": "Erro ao buscar comentários."}), 500
    
@app.route('/api/criar_chamado_azure', methods=['POST'])
@login_required
def criar_chamado_azure():
    try:
        data = request.get_json()
        id_chamado = data.get("id_chamado")
        responsavel = data.get("responsavel")
       

        response = supabase.table('chamados').select('*').eq('id_chamado', id_chamado).execute()
        if not response.data:
            return jsonify({"error": "Chamado não encontrado"}), 404

        chamado = response.data[0]
        status = chamado.get("status_chamado", "").strip().lower()

        if status == "fechado":
            print(f"[INFO] Chamado {id_chamado} está fechado. Nenhum card será criado.")
            return jsonify({"success": True, "message": "Chamado fechado.."}), 200

        anexos_raw = chamado.get("anexos")
        chamado_anexos_list = []
        if isinstance(anexos_raw, str):
            try:
                chamado_anexos_list = json.loads(anexos_raw)
                if not isinstance(chamado_anexos_list, list):
                    chamado_anexos_list = []
            except json.JSONDecodeError:
                chamado_anexos_list = []
                print(f"Erro ao converter anexos para lista: {anexos_raw}")
        elif isinstance(anexos_raw, list):
            chamado_anexos_list = anexos_raw

        from rotas import create_work_item

        result = create_work_item(
            titulo=chamado["titulo"],
            descricao=chamado["descricao"],
            empresa=chamado["empresa_chamado"],
            plataforma=responsavel,
            email=chamado["email_solicitante"],
            filial=chamado.get("filial_chamado", ""),
            chamado_anexos=chamado_anexos_list
        )

        if "id" in result:
            id_azure = result["id"]
            supabase.table('chamados').update({"id_chamado_azure": id_azure}).eq('id_chamado', id_chamado).execute()
            return jsonify({"success": True, "id_azure": id_azure}), 200
        else:
            return jsonify({"error": result}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# --- Rotas de Recuperação de Senha ---

@app.route('/recuperar-senha', methods=['GET', 'POST'])
def solicitar_recuperacao_senha():
    if request.method == 'POST':
        identifier = request.form.get('identifier')
        usuario = obter_usuario_por_email_tel(identifier)

        if not usuario:
            flash('Usuário não encontrado com o e-mail ou telefone informado.', 'danger')
            return redirect(url_for('solicitar_recuperacao_senha'))

        token = gerar_token_recuperacao()
        sucesso = salvar_token_recuperacao(usuario['id'], token)

        if not sucesso:
            flash('Erro ao gerar token de recuperação.', 'danger')
            return redirect(url_for('solicitar_recuperacao_senha'))

        link = f"{SITE_BASE_URL}/redefinir-senha/{token}"
        corpo_email = f"""
            <!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: 'Arial', sans-serif;
                        background-color: #f4f4f4;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 30px auto;
                        background-color: #ffffff;
                        padding: 30px;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                    }}
                    h2 {{
                        color: #333333;
                        margin-bottom: 20px;
                    }}
                    p {{
                        color: #555555;
                        font-size: 15px;
                        line-height: 1.6;
                    }}
                    .button {{
                        display: inline-block;
                        margin-top: 20px;
                        background-color: #007BFF;
                        color: white;
                        padding: 12px 24px;
                        text-decoration: none;
                        border-radius: 6px;
                        font-weight: bold;
                    }}
                    .footer {{
                        margin-top: 30px;
                        font-size: 13px;
                        color: #999999;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Recuperação de Senha</h2>
                    <p>Olá <strong>{usuario['nome']}</strong>,</p>
                    <p>Recebemos uma solicitação para redefinir a senha da sua conta. Para prosseguir com a alteração, clique no botão abaixo:</p>
                    <a class="button" href="{link}">Redefinir Senha</a>
                    <p>Se o botão acima não funcionar, você também pode copiar e colar este link em seu navegador:</p>
                    <p><a href="{link}">{link}</a></p>
                    <p>Este link é válido por <strong>1 hora</strong>.</p>
                    <p>Se você não solicitou essa alteração, pode ignorar este e-mail com segurança.</p>

                    <div class="footer">
                        &copy; {datetime.now().year} Sistema de Chamados • Todos os direitos reservados.
                    </div>
                </div>
            </body>
            </html>
            """

        enviar_email(usuario['email'], 'Recuperação de Senha', corpo_email)
        flash('Instruções enviadas para o e-mail informado.', 'success')
        return redirect(url_for('tela_login'))

    return render_template('recuperar_senha.html')

@app.route('/solicitar-recuperacao-senha', methods=['POST'])
def processar_recuperacao_senha():
    identifier = request.form.get('identifier', '').strip()
    
    if not identifier:
        flash("Por favor, informe seu e-mail ou telefone.", "error")
        return redirect(url_for('recuperar_senha'))

    user = obter_usuario_por_email_tel(identifier)

    if user:
        token = gerar_token_recuperacao()
        if salvar_token_recuperacao(user['id'], token):
            reset_link = f"{SITE_BASE_URL}/redefinir-senha/{token}"
            
            email_body_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
                    .container {{ background-color: #ffffff; margin: 20px auto; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); max-width: 600px; }}
                    .header {{ text-align: center; padding-bottom: 20px; border-bottom: 1px solid #eeeeee; }}
                    .header img {{ max-width: 150px; }}
                    .content {{ padding: 20px 0; line-height: 1.6; color: #333; }}
                    .button-container {{ text-align: center; padding: 20px 0; }}
                    .button {{ background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                    .footer {{ text-align: center; padding-top: 20px; border-top: 1px solid #eeeeee; font-size: 0.9em; color: #888; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <img src="{SITE_BASE_URL}/static/image/logo_login.png" alt="Logo do Sistema">
                        <h2>Recuperação de Senha</h2>
                    </div>
                    <div class="content">
                        <p>Olá <strong>{user.get('nome_completo', 'usuário')}</strong>,</p>
                        <p>Você solicitou a recuperação de senha para sua conta.</p>
                        <p>Para redefinir sua senha, por favor clique no botão abaixo:</p>
                        <div class="button-container">
                            <a href="{reset_link}" class="button">Redefinir Senha</a>
                        </div>
                        <p>Se o botão acima não funcionar, copie e cole o seguinte link em seu navegador:</p>
                        <p><a href="{reset_link}">{reset_link}</a></p>
                        <p>Este link é válido por 1 hora. Se você não solicitou esta redefinição de senha, por favor, ignore este e-mail.</p>
                    </div>
                    <div class="footer">
                        <p>Atenciosamente,<br>Equipe de Suporte do Sistema de Chamados</p>
                    </div>
                </div>
            </body>
            </html>
            """

            if user.get('email'):
                assunto = "Recuperação de Senha - Sistema de Chamados"
                if enviar_email(user['email'], assunto, email_body_html):
                    flash("Se o e-mail estiver cadastrado, as instruções de recuperação de senha foram enviadas. Verifique sua caixa de entrada e spam.", "info")
                else:
                    flash("Não foi possível enviar o e-mail de recuperação. Tente novamente mais tarde.", "error")
            elif user.get('telefone'):               
                flash("Se o telefone estiver cadastrado, as instruções de recuperação de senha foram enviadas via SMS.", "info")
            else:
                flash("Não foi possível encontrar um método de contato para este usuário.", "error")
        else:
            flash("Não foi possível iniciar o processo de recuperação de senha. Tente novamente.", "error")
            app_logger.error(f"Falha ao salvar token para user: {user.get('id')}")
    else:       
        flash("Se o e-mail ou telefone estiverem cadastrados, as instruções de recuperação de senha serão enviadas. Verifique sua caixa de entrada e spam.", "info")
        app_logger.warning(f"Tentativa de recuperação de senha para identificador não encontrado: {identifier}")

    return redirect(url_for('recuperar_senha'))
@app.route('/redefinir-senha/<token>', methods=['GET', 'POST'])
def redefinir_senha_confirmar(token):
    if request.method == 'POST':
        nova_senha = request.form.get('new_password')
        confirmar_senha = request.form.get('confirm_password')

        if not nova_senha or nova_senha != confirmar_senha:
            flash('As senhas não coincidem ou estão vazias.', 'danger')
            return redirect(request.url)

        usuario_id = verificar_token_recuperacao(token)
        if not usuario_id:
            flash('Token inválido ou expirado.', 'danger')
            return redirect(url_for('tela_login'))

        sucesso = atualizar_senha_usuario(usuario_id, nova_senha)
        if sucesso:
            flash('Senha redefinida com sucesso. Faça login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Erro ao redefinir a senha.', 'danger')
            return redirect(url_for('tela_login'))

    return render_template('redefinir_senha.html', token=token)
@app.route('/dashboard_data')
@login_required
def dashboard_data():
    try:
        usuario_email = session.get('email')
        agora = datetime.now(pytz.utc)
        quinze_dias_atras = agora - timedelta(days=15)

        fechados = supabase.table('chamados').select('*') \
            .eq('email_solicitante', usuario_email) \
            .eq('status_chamado', 'Fechado') \
            .gte('data_atualizacao', quinze_dias_atras.isoformat()) \
            .execute().data

        movimentacoes = supabase.table('movimentacoes_chamado').select('*') \
            .gte('data', quinze_dias_atras.isoformat()) \
            .execute().data

        comentarios = supabase.table('comentarios_chamados').select('chamado_id, data_hora') \
            .gte('data_hora', quinze_dias_atras.isoformat()) \
            .execute().data

        chamados_totais = supabase.table('chamados').select('status_chamado, data_atualizacao') \
            .gte('data_atualizacao', quinze_dias_atras.isoformat()) \
            .execute().data

        total_abertos = sum(1 for c in chamados_totais if c['status_chamado'].lower() == 'aberto')
        total_fechados = sum(1 for c in chamados_totais if c['status_chamado'].lower() == 'fechado')
        total_em_andamento = sum(1 for c in chamados_totais if c['status_chamado'].lower() == 'em andamento')

        return jsonify({
            "fechados": fechados,
            "movimentacoes": movimentacoes,
            "comentarios": comentarios,
            "grafico": {
                "abertos": total_abertos,
                "fechados": total_fechados,
                "em_andamento": total_em_andamento
            }
        })
    except Exception as e:
        print("Erro ao carregar dashboard:", e)
        return jsonify({"error": "Erro ao carregar dados do dashboard."}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard_real.html", usuario_nome=session.get('nome'))
@socketio.on('connect')
def handle_connect():
    app_logger.info('Cliente conectado')
    emit_dashboard_data()

def emit_dashboard_data():
    try:
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        quinze_dias_atras = datetime.now(fuso_horario) - timedelta(days=15)

        fechados = supabase.table('chamados').select('id_chamado, titulo, data_fechamento') \
            .not_.is_('data_fechamento', None) \
            .gte('data_fechamento', quinze_dias_atras.isoformat()) \
            .order('data_fechamento', desc=True).limit(5).execute().data

        movimentacoes = supabase.table('movimentacoes_chamado').select('*') \
            .gte('data', quinze_dias_atras.isoformat()) \
            .order('data', desc=True).limit(10).execute().data 

        comentarios = supabase.table('comentarios_chamados').select('chamado_id, data_hora') \
            .gte('data_hora', quinze_dias_atras.isoformat()) \
            .order('data_hora', desc=True).limit(5).execute().data 

        chamados_totais = supabase.table('chamados').select('status_chamado, data_atualizacao') \
            .gte('data_atualizacao', quinze_dias_atras.isoformat()) \
            .execute().data

        total_abertos = sum(1 for c in chamados_totais if c['status_chamado'].lower() == 'aberto')
        total_fechados = sum(1 for c in chamados_totais if c['status_chamado'].lower() == 'fechado')
        total_em_andamento = sum(1 for c in chamados_totais if c['status_chamado'].lower() == 'em andamento')

        dashboard_data = {
            "fechados": fechados,
            "movimentacoes": movimentacoes,
            "comentarios": comentarios,
            "grafico": {
                "abertos": total_abertos,
                "fechados": total_fechados,
                "em_andamento": total_em_andamento
            }
        }
        socketio.emit('dashboard_update', dashboard_data)
        app_logger.info('Dados do dashboard emitidos via SocketIO.')
    except Exception as e:
        app_logger.error(f"Erro ao emitir dados do dashboard: {e}")

@app.route('/api/usuarios', methods=['GET'])
@login_required
def get_usuarios():
    if session.get('acesso') not in ['admin']:
        return jsonify({'error': 'Acesso negado. Você não tem permissão para visualizar usuários.'}), 403
    try:
        response = supabase.table('usuarios').select('id, nome, email, empresa, funcao, acesso').execute()
        if response.data:
            return jsonify(response.data), 200
        return jsonify([]), 200
    except Exception as e:
        app_logger.error(f"Erro ao buscar usuários: {e}")
        return jsonify({'error': 'Erro ao buscar usuários.'}), 500

@app.route('/api/usuarios', methods=['POST'])
@login_required
def criar_usuario():
    try:
        if session.get('acesso') != 'admin':
            return jsonify({'error': 'Acesso negado. Apenas administradores podem gerenciar usuários.'}), 403
        
        data = request.get_json()
        campos_obrigatorios = ['nome', 'email', 'senha', 'empresa', 'funcao', 'acesso']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'error': f'Campo {campo} é obrigatório'}), 400

        response = supabase.table('usuarios').select('email').eq('email', data['email']).execute()
        if response.data:
            return jsonify({'error': 'Email já cadastrado no sistema'}), 400
        
        senha_hash = generate_password_hash(data['senha'])

        novo_usuario = {
            'nome': data['nome'],
            'email': data['email'],
            'senha': senha_hash,
            'empresa': data['empresa'],
            'funcao': data['funcao'],
            'acesso': data['acesso'],
            'telefone': data.get('telefone', ''),
            'data_criacao': datetime.now(pytz.utc).isoformat()
        }
        
        
        response = supabase.table('usuarios').insert(novo_usuario).execute()
        
        if response.data:            
            usuario_criado = response.data[0]
            if 'senha' in usuario_criado:
                del usuario_criado['senha']
            
            app_logger.info(f"Usuário {data['email']} criado por {session.get('email')}")
            return jsonify({'message': 'Usuário criado com sucesso', 'usuario': usuario_criado}), 201
        else:
            return jsonify({'error': 'Erro ao criar usuário'}), 500
            
    except Exception as e:
        app_logger.error(f"Erro ao criar usuário: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/usuarios/<string:usuario_id>', methods=['PUT'])
@login_required
def update_user(usuario_id):
    if session.get('acesso') != 'admin':
        return jsonify({'error': 'Acesso negado. Você não tem permissão para editar usuários.'}), 403

    data = request.json
    nome = data.get('nome')
    telefone = data.get('telefone')
    empresa = data.get('empresa')
    funcao = data.get('funcao')
    acesso = data.get('acesso')

    # Validação básica
    if not all([nome, telefone, empresa, funcao, acesso]):
        return jsonify({'error': 'Todos os campos são obrigatórios para atualização.'}), 400

    try:
        response = supabase.table('usuarios').update({
            'nome': nome,
            'telefone': telefone,
            'empresa': empresa,
            'funcao': funcao,
            'acesso': acesso
        }).eq('id', usuario_id).execute()

        if response.data:
            return jsonify({'message': 'Usuário atualizado com sucesso!'}), 200
        else:
            app_logger.error(f"Supabase retornou vazio ao atualizar usuário {usuario_id}. Erro: {response.error}")
            return jsonify({'error': 'Erro ao atualizar usuário.'}), 500
    except Exception as e:
        app_logger.error(f"Erro inesperado ao atualizar usuário {usuario_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor ao atualizar usuário.'}), 500

@app.route('/api/usuarios/<string:usuario_id>', methods=['DELETE'])
@login_required
def deletar_usuario(usuario_id):    
    try:
      
        if session.get('acesso') != 'admin':
            return jsonify({'error': 'Acesso negado. Apenas administradores podem gerenciar usuários.'}), 403
        
   
        response = supabase.table('usuarios').select('*').eq('id', usuario_id).execute()
        if not response.data:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        usuario = response.data[0]        
      
        if usuario_id == session.get('usuario_id'):
            return jsonify({'error': 'Você não pode deletar sua própria conta'}), 400
        
        
        response_chamados = supabase.table('chamados').select('id_chamado').eq('usuario_id', usuario_id).execute()
        if response_chamados.data:
            return jsonify({'error': 'Não é possível deletar usuário com chamados associados'}), 400
        
     
        response = supabase.table('usuarios').delete().eq('id', usuario_id).execute()
        
        if response.data:
            app_logger.info(f"Usuário {usuario['email']} (ID: {usuario_id}) deletado por {session.get('email')}")
            return jsonify({'message': 'Usuário deletado com sucesso'}), 200
        else:
            return jsonify({'error': 'Erro ao deletar usuário'}), 500
            
    except Exception as e:
        app_logger.error(f"Erro ao deletar usuário {usuario_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/usuarios/<string:usuario_id>', methods=['GET'])
@login_required
def get_usuario(usuario_id):
    if session.get('acesso') not in ['admin', 'suporte']:
        return jsonify({'error': 'Acesso negado. Você não tem permissão para visualizar este usuário.'}), 403
    try:
        response = supabase.table('usuarios').select('id, nome, email, telefone, empresa, funcao, acesso').eq('id', usuario_id).single().execute()
        if response.data:
            return jsonify(response.data), 200
        return jsonify({'error': 'Usuário não encontrado'}), 404
    except Exception as e:
        app_logger.error(f"Erro ao buscar usuário {usuario_id}: {e}")
        return jsonify({'error': 'Erro ao buscar dados do usuário.'}), 500

@app.route('/api/chamados_resolvidos', methods=['GET'])
@login_required
def chamados_resolvidos():
    try:
        user_email = session.get('email')
        if not user_email:
            return jsonify({"error": "Usuário não logado"}), 401

        response = supabase.table('chamados') \
            .select('id_chamado') \
            .eq('email_solicitante', user_email) \
            .eq('status_chamado', 'Fechado') \
            .execute()

        quantidade = len(response.data) if response.data else 0

        return jsonify({"quantidade_fechados": quantidade})

    except Exception as e:
        print(f"Erro ao buscar chamados resolvidos: {e}")
        return jsonify({"error": "Erro interno ao buscar chamados resolvidos"}), 500
@app.route('/api/chamados/<id_chamado>')
@login_required
def api_chamado(id_chamado):
    try:
        # Busca o chamado no banco de dados
        response = supabase.table('chamados').select('*').eq('id_chamado', id_chamado).single().execute()
        
        if not response.data:
            return jsonify({'error': 'Chamado não encontrado'}), 404
            
        chamado = response.data
        
        # Busca informações do solicitante
        email_solicitante = chamado.get('email_solicitante')
        solicitante = 'Não informado'
        if email_solicitante:
            user_response = supabase.table('usuarios').select('nome').eq('email', email_solicitante).single().execute()
            if user_response.data:
                solicitante = user_response.data.get('nome', 'Não informado')
        
        # Formata os dados para retorno
        dados_chamado = {
            'id_chamado': chamado.get('id_chamado'),
            'titulo': chamado.get('titulo'),
            'descricao': chamado.get('descricao'),
            'status_chamado': chamado.get('status_chamado'),
            'prioridade': chamado.get('prioridade'),
            'data_criacao': chamado.get('data_criacao'),
            'nome_solicitante': solicitante,
            'categoria': chamado.get('categoria'),
            'empresa_chamado': chamado.get('empresa_chamado'),
            'plataforma_chamado': chamado.get('plataforma_chamado'),
            'filial_chamado': chamado.get('filial_chamado')
        }
        
        return jsonify(dados_chamado), 200
        
    except Exception as e:
        print(f"Erro ao buscar chamado {id_chamado}: {e}")
        return jsonify({'error': 'Erro ao buscar detalhes do chamado'}), 500

@app.route('/admin_usuarios')
@login_required
def admin_usuarios():
    if session.get('acesso') != 'admin':
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'error')
        return redirect(url_for('menu_modulo'))
    return render_template('admin_usuarios.html')
@app.route('/cadastro_modal', methods=['GET'])
@login_required
def cadastro_modal():
    try:
        with app.open_resource('templates/tela_cadastro.html') as f:
            content = f.read().decode('utf-8')
        return Response(content, mimetype='text/html')
    except FileNotFoundError:
        app_logger.error("tela_cadastro.html não encontrado no diretório templates.")
        return "Conteúdo do formulário de cadastro não encontrado.", 404
    except Exception as e:
        app_logger.error(f"Erro ao ler tela_cadastro.html: {e}")
        return "Erro interno ao carregar o formulário.", 500
@app.route('/get_admin_usuarios_content', methods=['GET'])
@login_required
def get_admin_usuarios_content():
    if session.get('acesso') != 'admin':
        return "Acesso negado. Você não tem permissão para visualizar este conteúdo.", 403
    try:
        with app.open_resource('templates/admin_usuarios.html') as f:
            content = f.read().decode('utf-8')
        return Response(content, mimetype='text/html')
    except FileNotFoundError:
        app_logger.error("admin_usuarios.html não encontrado no diretório templates.")
        return "Conteúdo da administração de usuários não encontrado.", 404
    except Exception as e:
        app_logger.error(f"Erro ao ler admin_usuarios.html: {e}")
        return "Erro interno ao carregar o conteúdo.", 500

@app.route('/api/reset_password_email', methods=['POST'])
@login_required
def reset_password_email():
    if session.get('acesso') not in ['admin', 'atendente']:
        return jsonify({'success': False, 'message': 'Acesso negado.'}), 403

    data = request.get_json()
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'message': 'ID do usuário não fornecido.'}), 400

    try:
        user_data = obter_usuario_por_is(user_id)
        if not user_data:
            return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404

        token = gerar_token_recuperacao()
        if not salvar_token_recuperacao(user_id, token):
            return jsonify({'success': False, 'message': 'Erro ao gerar token de recuperação.'}), 500

        reset_link = f"{SITE_BASE_URL}/redefinir-senha/{token}"
        subject = "Redefinição de Senha - Sistema de Chamados"
        body_html = f"""
            <p>Olá {user_data['nome']},</p>
            <p>Recebemos uma solicitação para redefinir a senha da sua conta no Sistema de Chamados.</p>
            <p>Para redefinir sua senha, clique no link abaixo:</p>
            <p><a href="{reset_link}">Redefinir Senha</a></p>
            <p>Este link expirará em 1 hora.</p>
            <p>Se você não solicitou uma redefinição de senha, por favor, ignore este e-mail.</p>
            <p>Atenciosamente,</p>
            <p>Equipe de Suporte</p>
        """

        if enviar_email(user_data['email'], subject, body_html):
            return jsonify({'success': True, 'message': 'E-mail de recuperação enviado com sucesso!'}), 200
        else:
            return jsonify({'success': False, 'message': 'Falha ao enviar o e-mail de recuperação.'}), 500

    except Exception as e:
        app_logger.error(f"Erro ao solicitar reset de senha para o usuário {user_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500


