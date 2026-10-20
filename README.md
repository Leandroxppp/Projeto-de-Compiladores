# MiniPar 2026.2 — Compilador Educacional

Projeto de Compiladores — UFAL. Esta versão foi organizada para atender ao enunciado 2026.2, mantendo a cadeia de compilação e acrescentando **Fork/Join**, os testes paralelos 8–10 e uma **segunda interface Web com finalidade didática**.

## Entregas principais

- Analisador Léxico (tokens com linha/coluna e comentários `#`).
- Parser descendente recursivo e AST.
- Análise semântica com escopos, declarações e validação de `join`.
- Tabela de símbolos integrada ao analisador semântico.
- Geração TAC (código de três endereços).
- Geração C++20 e compilação automática via `g++ -O3 -pthread`.
- `PAR` mapeado para threads.
- `Fork`/`Join` explícitos na gramática, AST, semântico, TAC e backend C++.
- `c_channel`, `send` e `receive` com runtime TCP no C++ gerado.
- Interface terminal.
- Interface Web de desenvolvedor (`/dev`).
- Segunda Interface Web didática (`/learn`) com Tokens, AST hierárquica, Semântico, TAC, C++, compilação, download e execução.
- Testes 8, 9 e 10 em MiniPar.
- BNF 2026.2, UML, backlog e sprints.

## Estrutura

```text
MiniPar2026_2/
├── src/
│   ├── lexer.py
│   ├── parser.py
│   ├── ast_nodes.py
│   ├── semantic.py
│   ├── tac.py
│   ├── codegen.py
│   └── compiler.py
├── templates/
│   ├── index.html
│   ├── dev.html
│   └── learn.html
├── static/style.css
├── tests/
│   ├── teste1_calculadora_cliente.minipar / servidor.minipar
│   ├── teste2...teste7...
│   ├── teste8_avaliacao_4_nucleos.minipar
│   ├── teste9_5_nucleos_fractal.minipar
│   ├── teste10_6_nucleos_2_fractais.minipar
│   └── test_compiler.py
├── docs/
│   ├── uml.md
│   ├── product-backlog.md
│   └── referencias/
├── BNF-grammar-2026.2.md
├── main.py
├── app.py
└── test_orchestrator.py
```

## Instalação

Requisitos: Python 3.10+ e `g++` com C++20.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Interface Terminal

```bash
python main.py tests/teste8_avaliacao_4_nucleos.minipar --run
```

## Interfaces Web

```bash
python app.py
```

Abra:

- `http://127.0.0.1:5000/dev` — interface do desenvolvedor.
- `http://127.0.0.1:5000/learn` — nova interface didática.

A interface didática possui botões independentes para **Tokens**, **AST**, **Análise Semântica**, **TAC**, **C++**, **Compilar**, **baixar executável** e **Executar**.

As duas interfaces Web também aceitam **entrada padrão (`stdin`)**. Isso permite executar diretamente programas interativos, como o Teste 6. Ao carregar o Teste 6, uma entrada de exemplo é preenchida automaticamente e pode ser alterada antes da execução.

Para o **Teste 1**, ao carregar o cliente ou o servidor aparece um painel especial **Executar cliente + servidor**. Esse modo compila os dois programas, inicia o servidor e executa o cliente em `127.0.0.1`, mantendo a comunicação real por sockets TCP na porta `5055`. A execução em dois computadores continua disponível pelo terminal, informando no cliente o IPv4 da máquina servidora.

## Nova sintaxe Fork/Join

```minipar
seq {
    fork tarefaA on core(1) {
        print("A executando");
    }

    fork tarefaB on core(2) {
        print("B executando");
    }

    join(tarefaA, tarefaB);
}
```

A geração de C++ transforma cada `fork` em `std::thread` e cada `join` em `thread.join()`.

## Testes

Testes unitários:

```bash
python -m pytest -q
```

Integração dos programas `.minipar`:

```bash
python test_orchestrator.py
```

No ambiente de validação usado para preparar esta entrega, os testes unitários passaram e os **12 programas MiniPar incluídos** foram compilados com sucesso por `g++`. Também foi validada comunicação TCP em localhost entre os executáveis cliente/servidor do Teste 1.

## Observação sobre alocação em núcleo

A expressão `core(n)` gera uma `std::thread` e solicita afinidade com a CPU lógica indicada. No Windows, o runtime usa `SetThreadAffinityMask`; em sistemas POSIX/Linux, usa `pthread_setaffinity_np`. A afinidade restringe a thread ao processador lógico solicitado, enquanto o sistema operacional continua responsável pelo escalonamento temporal. A forma `computer(...)` fica representada sintaticamente para o cenário distribuído, enquanto a troca de dados entre máquinas é feita por `c_channel` com sockets TCP.

## Documentação

- `BNF-grammar-2026.2.md`: gramática consolidada e extensões Fork/Join.
- `docs/uml.md`: diagramas de componentes, classes e casos de uso (Mermaid).
- `docs/product-backlog.md`: Product Backlog e Sprints.
- `docs/referencias/`: arquivos fornecidos pelo professor usados como referência para os testes 8–10 e BNF 2026.1.

## Checklist de apresentação

1. Rodar `python -m pytest -q`.
2. Rodar `python test_orchestrator.py`.
3. Demonstrar um teste por terminal com `--run`.
4. Abrir `/dev` e mostrar o fluxo completo.
5. Abrir `/learn`, clicar em Tokens → AST → Semântico → TAC → C++.
6. Compilar, baixar o executável e executar.
7. Abrir `teste8`, `teste9` e `teste10` e explicar Fork/Join.
8. Mostrar BNF e UML no GitHub.

### Teste 1 — calculadora cliente/servidor

O cliente solicita o IP do servidor, a operação e os dois operandos pelo teclado. Para localhost, informe `127.0.0.1`. Em duas máquinas, execute o servidor em um computador e informe no cliente o IPv4 desse servidor. A porta usada é `5055`.
