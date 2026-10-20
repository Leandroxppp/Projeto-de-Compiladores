# Relatório Técnico — Compilador MiniPar 2026.2

## 1. Introdução

O MiniPar 2026.2 é um compilador educacional orientado a objetos que traduz programas MiniPar para C++20. A implementação segue uma pipeline clássica: análise léxica, análise sintática com construção da AST, análise semântica, geração TAC, geração de C++ e compilação nativa via `g++ -O3`.

A versão 2026.2 mantém as formas de interação do projeto anterior e acrescenta uma segunda interface Web voltada a alunos iniciantes, além da extensão da linguagem com `Fork` e `Join`.

## 2. Arquitetura geral

| Componente | Arquivo | Responsabilidade |
|---|---|---|
| Lexer | `src/lexer.py` | Converte caracteres em tokens com linha e coluna. |
| Parser | `src/parser.py` | Parser descendente recursivo e construção da AST. |
| AST | `src/ast_nodes.py` | Modelo orientado a objetos dos nós sintáticos. |
| Semântico | `src/semantic.py` | Escopos, declarações, uso de identificadores e validação Fork/Join. |
| TAC | `src/tac.py` | Código intermediário de três endereços. |
| Codegen | `src/codegen.py` | C++20, threads, sockets e compilação g++. |
| Fachada | `src/compiler.py` | Orquestra todas as fases. |
| Terminal | `main.py` | Compilação e execução via CLI. |
| Web | `app.py` | APIs e duas interfaces Web. |

## 3. Linguagem MiniPar 2026.2

A linguagem preserva blocos `seq`/`par`, estruturas de controle, funções, classes, objetos, listas, entrada/saída e canais. A versão 2026.2 acrescenta:

```minipar
fork tarefaA on core(1) {
    print("subtarefa A");
}
fork tarefaB on core(2) {
    print("subtarefa B");
}
join(tarefaA, tarefaB);
```

O parser cria nós `Fork` e `Join`. O semântico garante que nomes de subtarefas não sejam duplicados e que `join` só referencie subtarefas conhecidas. O TAC contém instruções `FORK`, `END_FORK` e `JOIN`. No C++ gerado, cada `fork` produz `std::thread`, cada `join` chama `join()` e `core(n)` solicita afinidade com a CPU lógica indicada por meio de `SetThreadAffinityMask` (Windows) ou `pthread_setaffinity_np` (POSIX/Linux).

## 4. Analisador Léxico — pseudocódigo

```text
TOKENIZE(fonte)
  enquanto não chegar ao fim
    ignorar espaços e comentários iniciados por #
    se letra/_: ler identificador e classificar palavra reservada
    senão se dígito: ler número inteiro/real
    senão se aspas: ler literal string e escapes
    senão: reconhecer operador/delimitador de 1 ou 2 caracteres
    produzir Token(tipo, lexema, linha, coluna)
  produzir EOF
```

## 5. Analisador Sintático — pseudocódigo

```text
PARSE(tokens)
  programa = []
  enquanto token != EOF
    programa.adicionar(PARSE_STATEMENT())
  retornar Program(programa)

PARSE_STATEMENT()
  selecionar produção por token inicial
  construir nó AST correspondente
  para expressões, aplicar níveis de precedência:
    OR -> AND -> igualdade -> comparação -> termo -> fator -> unário -> pós-fixa
```

## 6. Analisador Semântico — pseudocódigo

```text
ANALYZE(AST)
  criar pilha de escopos
  pré-cadastrar funções e classes globais
  visitar recursivamente a AST
  ao declarar: verificar redeclaração no escopo atual
  ao usar ID: buscar do escopo interno para o externo
  ao encontrar Fork: registrar nome da subtarefa
  ao encontrar Join: validar que cada subtarefa existe
  retornar lista de erros
```

## 7. Tabela de Símbolos — pseudocódigo

```text
ENTER_SCOPE(): empilhar novo mapa
DEFINE(nome, tipo): inserir no mapa do topo
LOOKUP(nome): procurar do topo até o escopo global
LEAVE_SCOPE(): desempilhar mapa atual
```

## 8. Código Intermediário TAC

Exemplo:

```text
FORK tarefaA ON core(1)
# FORK BEGIN
PRINT 'A'
# FORK END
END_FORK tarefaA
JOIN tarefaA
```

Expressões complexas criam temporários `t1`, `t2`, ... e estruturas de controle usam rótulos e saltos condicionais.

## 9. Geração de código C++

O backend gera C++20. Blocos paralelos e Fork usam `std::thread` com captura por valor; `core(n)` aplica afinidade de CPU lógica; saída concorrente é protegida por `std::mutex`; canais utilizam sockets TCP. O arquivo alvo é compilado com `g++ -std=c++20 -O3 -pthread` e, no Windows, `-lws2_32` para Winsock.

## 10. Interfaces

### 10.1 Terminal

`main.py` permite compilar um arquivo `.minipar`, salvar TAC/C++ e opcionalmente executar o binário.

### 10.2 Web para desenvolvedor

A rota `/dev` oferece editor e abas compactas para Tokens, AST JSON, semântico, TAC, C++ e saída.

### 10.3 Segunda Web didática

A rota `/learn` separa cada etapa por botão e apresenta uma AST hierárquica, com nós e relações pai-filho, evitando exibir apenas JSON. O usuário pode estudar a pipeline progressivamente e ainda compilar, executar e baixar o executável.

## 11. Product Backlog e Sprints

Ver `docs/product-backlog.md`.

## 12. UML

Ver `docs/uml.md`, contendo casos de uso, diagrama de componentes e diagrama de classes dos componentes.

## 13. Testes de integração

O script `test_orchestrator.py` percorre todos os arquivos `.minipar` em `tests/`, executa Lexer → Parser → Semântico → TAC → C++ → g++ e informa sucesso/falha.

Os testes 8–10 foram convertidos para MiniPar com Fork/Join:

- Teste 8: quatro subtarefas de avaliação (4 núcleos lógicos).
- Teste 9: quatro avaliadores e uma subtarefa de fractal (5 núcleos lógicos).
- Teste 10: quatro avaliadores e duas subtarefas de fractais (6 núcleos lógicos).

No ambiente local de preparação, os 12 programas incluídos foram compilados com sucesso. Os executáveis dos testes 2–10 foram executados e o Teste 1 foi validado com cliente e servidor TCP em localhost (`Servidor recebeu: 1|12|8`).

## 14. Tecnologias utilizadas

Python 3, Flask, HTML/CSS/JavaScript, C++20, g++, `std::thread`, `std::mutex`, sockets TCP e pytest.

## 15. Como reproduzir

```bash
pip install -r requirements.txt
python -m pytest -q
python test_orchestrator.py
python app.py
```

## 16. Conclusão

A versão entrega uma base completa e documentada do MiniPar 2026.2, com extensão sintática e semântica para Fork/Join, geração de paralelismo real por threads, comunicação TCP, pipeline completa de compilação e uma nova interface Web específica para ensino das fases do compilador.
