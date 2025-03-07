import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def enviar_email(destinatario, id_chamado):
    nome_solicitante = destinatario.split("@")[0] if destinatario else "Usuário"
    remetente = "jonathanwillian710@gmail.com"
    senha = "ipwz cujh frdv ivjj"

    assunto = "Chamado Criado com Sucesso!"
    corpo = f"""Olá {nome_solicitante},

                Seu chamado foi criado com sucesso! 🚀

                🔹 **ID do Chamado:** {id_chamado}

                Nossa equipe analisará sua solicitação em breve.

                Atenciosamente,  
                Suporte T.I BRAVEO"""

    msg = MIMEMultipart()
    msg['From'] = remetente  
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))  

    print(f"Remetente: {remetente}")
    print(f"Destinatário: {destinatario}")
    print(f"Assunto: {assunto}")
    print(f"Corpo: {corpo}")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(remetente, senha)
            server.sendmail(remetente, destinatario, msg.as_string())
        
        print(f"✅ E-mail enviado com sucesso para {destinatario}")
        #return True
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        #return False

    #except smtplib.SMTPAuthenticationError:
     #   print("❌ Erro de autenticação! Verifique a senha de aplicativo.")
      #  return False
   
