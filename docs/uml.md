# UML — MiniPar 2026.2

## Diagrama de Componentes

```mermaid
flowchart LR
  UI1[Interface Terminal] --> C[compiler.py / compile_source]
  UI2[Web Desenvolvedor] --> C
  UI3[Web Didática] --> C
  C --> L[Lexer]
  L --> P[Parser]
  P --> AST[AST / ast_nodes.py]
  AST --> S[SemanticAnalyzer]
  S --> ST[Tabela de símbolos / escopos internos]
  AST --> T[TACGenerator]
  AST --> G[CppCodeGenerator]
  G --> RT[Runtime C++: threads, afinidade e sockets]
  G --> GCC[g++ -std=c++20 -O3 -pthread]
  GCC --> EXE[Executável]
```

## Diagrama de Classes dos Componentes Implementados

```mermaid
classDiagram
  class Token {
    +TT type
    +String lexeme
    +int line
    +int col
  }
  class Lexer {
    -String source
    +tokenize() List~Token~
  }
  class Parser {
    -List~Token~ tokens
    +parse() Program
  }
  class Program
  class ASTNode
  class SemanticAnalyzer {
    -scopes
    -functions
    -classes
    -forks
    +analyze(AST) List~String~
  }
  class TACGenerator {
    +generate(AST) String
  }
  class CppCodeGenerator {
    +generate(AST) String
  }

  Lexer --> Token : produz
  Parser --> Token : consome
  Parser --> Program : constrói
  Program --|> ASTNode
  SemanticAnalyzer --> ASTNode : analisa
  TACGenerator --> ASTNode : percorre
  CppCodeGenerator --> ASTNode : percorre
```

> Observação: a tabela de símbolos é implementada internamente no `SemanticAnalyzer` por uma pilha de escopos (mapas/dicionários), e não como uma classe separada.

## Casos de Uso

```mermaid
flowchart TB
  U((Aluno / Desenvolvedor)) --> E[Editar programa MiniPar]
  U --> TK[Exibir Tokens]
  U --> AST[Visualizar AST didática]
  U --> SEM[Executar análise semântica]
  U --> TAC[Visualizar TAC]
  U --> CPP[Visualizar C++ gerado]
  U --> COMP[Compilar]
  U --> DOWN[Baixar executável]
  U --> RUN[Executar]
```
