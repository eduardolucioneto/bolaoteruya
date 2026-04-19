# Deploy no PythonAnywhere

## 1. Criar conta
Acesse https://www.pythonanywhere.com e crie uma conta gratuita.

## 2. Configurar ambiente
No Bash console do PythonAnywhere:

```bash
# Criar virtualenv
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r https://SEU_USERNAME.pythonanywhere.com/requirements.txt
```

Na verdade, faça assim:

```bash
# Clone o repositório (se usar git) ou faça upload dos arquivos
# Criar virtualenv pelo painel: UI > Virtualenvs > + New virtualenv
# Nome: venv

# Instalar dependências no console:
pip install Django>=5.1 psycopg[binary]>=3.2 python-dotenv>=1.0 Pillow>=10.4 gunicorn
```

## 3. Configurar Web App

No painel PythonAnywhere, vá em **Web** > **Add a new web app**:

1. Selecione **Manual configuration**
2. Escolha **Python 3.12** (ou versão disponível)
3. Clique no link para configurar o virtualenv

### Configurações do Web App:

**WSGI configuration file** (clique no link):
```python
import os
import sys

# Seu projeto
path = '/home/SEU_USERNAME/SEU_PROJETO'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['SECRET_KEY'] = 'sua-chave-secreta-aqui'
os.environ['DEBUG'] = 'False'
os.environ['ALLOWED_HOSTS'] = 'SEU_USERNAME.pythonanywhere.com'

# Para SQLite (usar banco local)
os.environ['USE_SQLITE'] = 'True'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

## 4. Arquivos estáticos

No painel **Web** > **Static files**:
- URL: `/static/`
- Path: `/home/SEU_USERNAME/SEU_PROJETO/staticfiles`

Execute no console:
```bash
python manage.py collectstatic
```

## 5. Banco de dados

Execute migrações no console Bash:
```bash
python manage.py migrate
python manage.py createsuperuser
```

## 6. Variáveis de ambiente

No arquivo `.env` no seu projeto:
```env
SECRET_KEY=sua-chave-super-secreta-aqui
DEBUG=False
ALLOWED_HOSTS=seuusername.pythonanywhere.com
USE_SQLITE=True
```

## 7. Recarregar

No painel **Web**, clique em **Reload** para aplicar as mudanças.

## Banco de dados SQLite

Como o PythonAnywhere gratuito não oferece banco PostgreSQL, o projeto está configurado para usar SQLite automaticamente se `USE_SQLITE=True`.

## Problemas comuns

1. **Erro 500**: Verifique os logs em **Web** > **Logs**
2. **Static files 404**: Execute `collectstatic` e configure o path corretamente
3. **Database error**: Verifique se migrou com `python manage.py migrate`