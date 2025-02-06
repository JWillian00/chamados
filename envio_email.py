import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

def enviar_email(destinatario, id_chamado):
    #email = requests.form["email"]
    nome_solicitante = destinatario.split("@")[0] if destinatario else "Usuário"
    remendente = "jonathanwillian710@gmail.com"
    senha = "cvtz zvul ipxn afdx"

    assunto = "Chamado Criado com Sucesso!"
    corpo = f"""Olá {nome_solicitante} ,
                    Seu chamado foi criado com sucesso!
                    🔹 ID do Chamado: {id_chamado}

                    Nossa equipe analisará sua solicitação em breve. 
                    Caso precise de mais informações, responda a este e-mail.



                    Atenciosamente,
                    Suporte T.I BRAVEO"""

    msg = MIMEMultipart()
    msg['From'] = remendente            
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(remendente, senha)
            server.sendmail(remendente, destinatario, msg.as_string())
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False