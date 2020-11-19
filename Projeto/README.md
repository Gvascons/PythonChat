### Chat

Esse é um chat server-client onde vários usuários podem se conectar e enviar mensagens públicas ou privadas

#### Alunos

Marcos Monteiro (mmmb@cin.ufpe.br)
João Gabriel Vasconcelos (jgav@cin.ufpe.br)

#### Requisitos

Para rodar estes programas, é necessários ter o [Python 3](https://www.python.org/downloads/) instalado.

#### Comandos

1) `list`: Lista todos os usuários ativos no chat
2) `send -all <mensagem>`: Envia mensagens para todos os usuários no chat
3) `send -user <usuário> <mensagem>`: Envia uma mensagem para um usuário específico
4) `bye`: Desconecta do chat


#### Rodando o servidor localmente

Na pasta do arquivo, rode o seguinte comando:
```bash
$ python3 server.py 127.0.0.1 7070
```
Aqui, a porta `7070` pode ser modificada para qualquer outra que não esteja sendo utilizada.

#### Rodando o cliente localmente

Na pasta do arquivo, rode o seguinte comando:
```bash
$ python3 client.py 127.0.0.1 7070 username
```
A porta precisa ser a mesma do servidor, e o username pode ser escolhido arbitrariamente pelo usuário. O cliente pode ser rodado em vários terminais diferentes para simular diferentes usuários.