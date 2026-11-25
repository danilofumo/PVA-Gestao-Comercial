# PVA-Gestão Comercial

Aplicação web inicial em Django para gestão de pequenos estabelecimentos.

## Incluído
- Registo de proprietário e estabelecimento
- Criação e desativação de trabalhadores
- Catálogo de produtos e stock
- Registo de vendas por trabalhador
- Atualização de stock na venda
- Caixas individuais e comuns
- Registo de despesas pelo proprietário
- Relatório financeiro básico
- Separação de dados por estabelecimento nas páginas da aplicação

## Instalação no Android com Termux

1. Instala Termux de fonte oficial (F-Droid ou GitHub).
2. No Termux:
   ```bash
   pkg update && pkg upgrade -y
   pkg install python -y
   ```
3. Extrai o ZIP numa pasta acessível.
4. Entra na pasta do projeto e executa:
   ```bash
   python -m pip install -r requirements.txt
   python manage.py migrate
   python manage.py runserver
   ```
5. Abre `http://127.0.0.1:8000/` no navegador do mesmo telemóvel.
6. Cria a conta do proprietário.

## Teste inicial recomendado
1. Regista um estabelecimento.
2. Cria um trabalhador no menu Trabalhadores.
3. Cria um produto com stock inicial.
4. Abre uma caixa individual como trabalhador ou uma caixa comum como proprietário.
5. Regista uma venda com a conta do trabalhador.
6. Confirma a redução do stock e consulta as vendas no painel do proprietário.

## Limitações e segurança
Esta é uma versão inicial de desenvolvimento, não uma instalação pronta para gerir dinheiro real em produção.
- Usa SQLite local durante os testes. Para alojamento online e vários utilizadores simultâneos, migra para PostgreSQL.
- Antes de publicar: define `PVA_SECRET_KEY` forte, `PVA_DEBUG=0`, configura `ALLOWED_HOSTS`, HTTPS, cookies seguros, backups e monitorização.
- Faz revisão de segurança e testes de permissões antes de utilizar comercialmente.
- Não partilhes o ficheiro `db.sqlite3`, palavras-passe ou chaves secretas.
- O fecho de caixa desta versão compara fundo inicial + vendas totais; a reconciliação por método de pagamento e movimentos de entrada/saída será uma melhoria seguinte.
- As operações financeiras e stock precisam de auditoria adicional e testes de concorrência antes de produção.

## Convites individuais de trabalhadores (protótipo)

A área de trabalhadores permite criar uma conta pendente, guardar o telefone, gerar um convite assinado válido por 48 horas e abrir uma mensagem preparada para WhatsApp. O trabalhador define a sua própria palavra-passe no convite. O proprietário não precisa de partilhar a sua palavra-passe.

**Importante:** enquanto o projecto estiver a correr apenas em `127.0.0.1` no telemóvel do proprietário, o link de convite não é acessível no telemóvel do trabalhador. Só enviar convites depois de publicar o sistema num servidor HTTPS com domínio/endereço público. O WhatsApp é aberto pelo utilizador; o sistema não envia mensagens automaticamente. O telefone ainda não é verificado por SMS/OTP.

Depois de substituir os ficheiros no Termux, executar:

```bash
python manage.py makemigrations core
python manage.py migrate
```

Criar um trabalhador de teste, abrir o link no WhatsApp apenas depois da publicação online e verificar que a conta fica activa após definir uma palavra-passe. Antes de produção, configurar `DEBUG=False`, `SECRET_KEY` segura, `ALLOWED_HOSTS`, HTTPS, cookies seguros, base de dados PostgreSQL, backups e testes de permissões.
