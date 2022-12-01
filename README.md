# Automatizador de impressão para o CUPS da SESDF

# Requesitos
 - Ter o python 3 instalado
 - Possuir o chrome instalado

Após ter instalado o python, abra uma nova instância do terminal e execute os seguintes comandos:
```bash
python --version
```
```bash
pip --version
```
Se nenhum erro emergir do terminal, então pode-se seguir para a próxima etapa.

# Como usar

Baixa o arquivo usando este [link](https://github.com/zeroCass/ses_cups_py/archive/refs/heads/main.zip) e extraia para um local de sua preferência.
Entre na pasta e modifique o arquivo env.sample com as seguintes configurações:
 * Abra o arquivo e coloque o endereço da URL da página JOBS do CUPS em MAIN_PAGE (Ex: MAIN_PAGE='http://URL/jobs').
 * Salve e renomeie o arquivo para .env.
Após isso, abra o CMD ou POWERSHELL do Windows de tal forma que esteja no mesmo diretório do arquivo .env, selenium_app.py e requirements.txt.
Caso não saiba fazer isso, basta copiar o endereço do diretorio (Ex: C:\Users\Usuario\DiretorioQualquer\ses_cups\) e digitar o comando **cd endereçoDoSeuDiretorio** no terminal CMD ou POWERSHELL aberto e apertar enter.

Agora, basta digiar o seguinte comando no terminal CMD/POWERSHELL:
```bash
pip install -r requirements.txt
```

Após a instalação dos pacotes estiverem concluídas basta executar o programa. Para isso, digite o seguinte comando no terminal:
```bash
python selenium_app.py
```

# Como o programa funciona

Este programa irá baixar uma versão atual do chrome de maneira virtual, pois o framework **Selenium** irá utilizá-lo no background para executar o chrome de maneira ''stealth''. O selenium simula clicks e inputs do teclado para realizar a tarefa repetitiva que é ter que restaurar a URL das impressoras que tiverem algum problema de rede resultando assim no acúmula de fila no servidor.

Sempre que um trabalho fica por mais de 2 minutos na fila do CUPS, o programa irá realizar um ping de teste no computador da impressora. Se o resultado for positivo, ele realiza a atualização da URL. Caso contrário, se assume que o computador está desligado e/ou fora de rede, então a impressão é cancelada. 

Como se sabe, a URL da impressora que utiliza do protocolo SMB irá variar depende do do domínio na qual o computador está inserido. Sendo assim, o programa reconhece essa variável de acordo com o hostname e localização da impressora (``` if 'saude.df.gov.br' in printer['hostname'] and 'UPA' not in printer['location'] ```), se for tiver saude.df.gov.br em seu hostname e não estiver em uma UPA, então está no domínio da SES, caso contrário está no IGES. Portanto, é importante que sempre que possível as impressoras tenham um hostname associado e não um IP.


# Problemas conhecidos e possíveis problemas no futuro
Se o programa estiver apresentando o erro: ** Error: name 're' is not defined **, então execute o script utilizando o arquivo ** selenium2_app.py **, da seguinte forma:
```bash
python selenium2_app.py
```


- Se a fila de impressão tiver mais de 100 trabalhos presos, o programa não irá funcionar. Portanto, limpe alguns trabalhos manualmente e depois execute o programa.
- Futuramente a SES irá transiocionar os nomes das impressoras para um novo padrão (Ex: PR-12345678). Esse novo padrão pode fazer com que o programa não execute corretamente. Portanto, se este for o caso, recomendo que abra uma ISSUE aqui no GitHub informando os erros presentes no proprio terminal OU abra um PULL REQUEST com um código que apresente alterações que solucione esse impasse.
