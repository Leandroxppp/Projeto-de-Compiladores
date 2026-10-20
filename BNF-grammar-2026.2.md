# Gramática BNF — MiniPar 2026.2

Esta versão mantém a base sintática da MiniPar 2026.1 e documenta as extensões efetivamente implementadas em 2026.2, em especial **Fork**, **Join**, alocação de subtarefas em `core(...)`/`computer(...)`, comunicação por `c_channel`, orientação a objetos, listas e chamadas à biblioteca nativa.

> Observação: as chamadas de biblioteca (`field`, `to_number`, `exp`, `len`, etc.) seguem a mesma sintaxe de qualquer chamada de função: um identificador seguido de `(...)`. A validade desses nomes é verificada semanticamente como função nativa; portanto, não é necessário criar uma produção sintática exclusiva para cada nome.

```bnf
<programa> ::= { <declaracao_global> | <comando> }

<declaracao_global> ::= <declaracao_classe>
                     | <declaracao_funcao>
                     | <declaracao_variavel>

<declaracao_variavel> ::= "var" <ID> [ "=" <expressao> ] ";"
                       | <tipo> <ID> [ "=" <expressao> ] ";"

<declaracao_sem_ponto_virgula> ::= "var" <ID> [ "=" <expressao> ]
                                 | <tipo> <ID> [ "=" <expressao> ]

<tipo> ::= "number" | "int" | "float" | "string" | "bool" | "void" | "list" | "dict"

<declaracao_funcao> ::= "func" <ID> "(" [ <parametros> ] ")" <bloco>
<parametros> ::= [ <tipo> ] <ID> { "," [ <tipo> ] <ID> }

<declaracao_classe> ::= "class" <ID> [ "extends" <ID> ] "{" { <membro_classe> } "}"
<membro_classe> ::= <declaracao_variavel> | <declaracao_funcao>

<comando> ::= <bloco>
            | <bloco_seq>
            | <bloco_par>
            | <declaracao_variavel>
            | <atribuicao>
            | <if>
            | <while>
            | <for>
            | <print>
            | <send>
            | <return>
            | "break" ";"
            | "continue" ";"
            | <fork>
            | <join>
            | <expressao> ";"

<bloco> ::= "{" { <comando> } "}"
<bloco_seq> ::= ("seq" | "SEQ") <bloco>
<bloco_par> ::= ("par" | "PAR") <bloco>

<atribuicao> ::= <alvo_atribuicao> "=" <expressao> ";"
<atribuicao_sem_ponto_virgula> ::= <alvo_atribuicao> "=" <expressao>
<alvo_atribuicao> ::= <posfixa>

<fork> ::= ("fork" | "Fork") <ID> "on" <alvo_fork> <bloco> [ ";" ]
<alvo_fork> ::= "core" "(" <expressao> ")"
              | "computer" "(" <expressao> ")"

<join> ::= ("join" | "Join") "(" <ID> { "," <ID> } ")" ";"
         | ("join" | "Join") <ID> { "," <ID> } ";"

<if> ::= "if" "(" <expressao> ")" <comando> [ "else" <comando> ]
<while> ::= "while" "(" <expressao> ")" <comando>

<for> ::= "for" "(" [ <inicializacao> ] ";" [ <expressao> ] ";" [ <incremento> ] ")" <comando>
<inicializacao> ::= <declaracao_sem_ponto_virgula>
                  | <atribuicao_sem_ponto_virgula>
                  | <expressao>
<incremento> ::= <atribuicao_sem_ponto_virgula> | <expressao>

<print> ::= "print" "(" [ <expressao> { "," <expressao> } ] ")" ";"
<send> ::= "send" "(" <expressao> { "," <expressao> } ")" ";"
<return> ::= "return" [ <expressao> ] ";"

<expressao> ::= <ou>
<ou> ::= <e> { "||" <e> }
<e> ::= <igualdade> { "&&" <igualdade> }
<igualdade> ::= <comparacao> { ("==" | "!=") <comparacao> }
<comparacao> ::= <termo> { ("<" | "<=" | ">" | ">=") <termo> }
<termo> ::= <fator> { ("+" | "-") <fator> }
<fator> ::= <unario> { ("*" | "/" | "%") <unario> }
<unario> ::= ("!" | "-") <unario> | <posfixa>

<posfixa> ::= <primaria> { <chamada_sufixo> | <propriedade> | <indice> }
<chamada_sufixo> ::= "(" [ <argumentos> ] ")"
<argumentos> ::= <expressao> { "," <expressao> }
<propriedade> ::= "." <ID>
<indice> ::= "[" <expressao> "]"

<primaria> ::= <NUMBER>
             | <STRING>
             | "true"
             | "false"
             | <ID>
             | "this"
             | "new" <ID> "(" [ <argumentos> ] ")"
             | "c_channel" "(" <expressao> "," <expressao> ")"
             | "receive" "(" <expressao> ")"
             | "input" "(" [ <expressao> ] ")"
             | <literal_lista>
             | "(" <expressao> ")"

<literal_lista> ::= "[" [ <expressao> { "," <expressao> } ] "]"
```

## Identificadores e literais

- `<ID>` representa um identificador válido da linguagem.
- `<NUMBER>` representa literal numérico inteiro ou real reconhecido pelo lexer.
- `<STRING>` representa literal textual entre aspas duplas, com os escapes suportados pelo lexer.
- Comentários de linha iniciados por `#` são ignorados pelo lexer.

## Semântica de Fork/Join

- `fork tarefa on core(n) { ... }`: cria uma subtarefa concorrente e solicita associação ao núcleo indicado.
- `fork tarefa on computer("IP") { ... }`: registra um alvo remoto lógico; a troca de dados entre computadores ocorre por `c_channel`/sockets.
- `join(t1, t2, ...)`: bloqueia a thread pai até que todas as subtarefas indicadas terminem.
- A geração C++ usa `std::thread`; para `core(n)`, o runtime aplica afinidade de thread quando suportada pelo sistema operacional.
- As subtarefas são geradas com captura por valor no C++ (`[=]() mutable`), evitando compartilhamento implícito por referência. Dados entre computadores devem ser trocados por mensagens via canais.

## Comunicação por `c_channel`

`c_channel(host, porta)` cria a descrição de um canal TCP. `send(canal, ...)` serializa os argumentos em uma mensagem separada por `|`; `receive(canal)` recebe uma mensagem textual.

A implementação é bidirecional no mesmo socket TCP: no cliente, `send(...)` mantém a conexão aberta para um `receive(...)` posterior; no servidor, `receive(...)` mantém a conexão aceita aberta para o `send(...)` de resposta.

## Biblioteca nativa reconhecida semanticamente

Os nomes abaixo são reconhecidos pelo analisador semântico como funções nativas. Sintaticamente, todos seguem a produção genérica de chamada `<ID> "(" ... ")"` já coberta por `<posfixa>` e `<chamada_sufixo>`.

```text
field(texto, indice)
to_number(texto)
exp(x)
sqrt(x)
pow(base, expoente)
sin(x)
cos(x)
tan(x)
log(x)
input_text([prompt])
input_list([prompt])
format_list(lista)
len(lista)
now_seconds()
cpu_work(seed)
mandelbrot_ascii()
sierpinski_ascii()
```

### Funções usadas no Teste 1

- `field(texto, indice)`: obtém o campo de índice `indice` de uma string separada por `|`, iniciando em 0.
- `to_number(texto)`: converte texto numérico para `number`.
- `input_text(prompt)`: lê uma linha textual do teclado; é usada pelo cliente para informar dinamicamente o IP do servidor.

A regra de negócio da calculadora — soma, subtração, multiplicação e divisão — permanece escrita no programa MiniPar do servidor, e não embutida no runtime.

## Biblioteca matemática

`exp`, `sqrt`, `pow`, `sin`, `cos`, `tan` e `log` são traduzidas para operações correspondentes da biblioteca matemática do C++ gerado. No Teste 4, `exp` é usada na função sigmoide.

## Utilitários dos testes

- `input_list`: lê uma sequência numérica e a converte para `list`.
- `format_list`: formata uma lista para exibição.
- `len`: retorna o tamanho de uma lista.
- `now_seconds`: retorna uma medida de tempo de alta resolução usada nos benchmarks.
- `cpu_work`: executa carga computacional usada nos testes de paralelismo.
- `mandelbrot_ascii`: gera a representação ASCII do conjunto de Mandelbrot usada nos testes 9 e 10.
- `sierpinski_ascii`: gera a representação textual do tapete de Sierpinski usada no teste 10.

## Relação com a MiniPar 2026.1

O arquivo `docs/referencias/BNF-MiniPar2026.1-original.md` preserva a gramática de referência anterior. Este arquivo `BNF-grammar-2026.2.md` documenta a versão efetivamente implementada no compilador atual e as extensões usadas pelos testes de 2026.2.
