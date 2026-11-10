from __future__ import annotations
import re
from dataclasses import fields, is_dataclass
from .ast_nodes import *

class SemanticError(Exception): pass

# Tipos primitivos da linguagem (int/float contam como number).
TIPO_DECLARADO={'int':'number','number':'number','float':'number','string':'string','bool':'bool','list':'list'}
NOME_TIPO={'number':'número','string':'texto','bool':'booleano','list':'lista'}
# Para cada tipo declarado, quais tipos de valor NAO podem ser atribuidos a ele.
# (number e bool se misturam porque o C++ gerado aceita a conversao.)
INCOMPATIVEL={'number':{'string','list'},'string':{'number','bool','list'},'bool':{'string','list'},'list':{'number','string','bool'}}
FUNCOES_NUMERICAS={'to_number','exp','sqrt','pow','sin','cos','tan','log','len','now_seconds','cpu_work'}
class SemanticAnalyzer:
    def __init__(self): self.scopes=[{}]; self.types=[{}]; self.functions={}; self.classes={}; self.forks={}; self.joined=set(); self.errors=[]
    def enter(self): self.scopes.append({}); self.types.append({})
    def leave(self): self.scopes.pop(); self.types.pop()
    def define(self,name,kind='var',typ=None):
        if name in self.scopes[-1]: self.errors.append(f"Identificador '{name}' redeclarado no mesmo escopo")
        self.scopes[-1][name]=kind; self.types[-1][name]=typ   # typ: 'number'|'string'|'bool'|'list'|None (desconhecido)
    def exists(self,name):
        native={'field','to_number','exp','sqrt','pow','sin','cos','tan','log','input_text','input_list','format_list','len','now_seconds','cpu_work','mandelbrot_ascii','sierpinski_ascii'}
        return any(name in s for s in reversed(self.scopes)) or name in self.functions or name in self.classes or name in native
    def analyze(self,node): self.visit(node); return self.errors
    def visit(self,n):
        if n is None:return
        m=getattr(self,'v_'+n.__class__.__name__,None)
        if m:return m(n)
        if is_dataclass(n):
            for f in fields(n):
                v=getattr(n,f.name)
                if isinstance(v,ASTNode): self.visit(v)
                elif isinstance(v,list):
                    for x in v:
                        if isinstance(x,ASTNode): self.visit(x)
    def v_Program(self,n):
        for s in n.statements:
            if isinstance(s,FuncDecl): self.functions[s.name]=s
            if isinstance(s,ClassDecl): self.classes[s.name]=s
        for s in n.statements:self.visit(s)
    def v_Block(self,n):
        self.enter()
        for s in n.statements:self.visit(s)
        self.leave()
    def v_VarDecl(self,n):
        self.visit(n.value)
        declared=TIPO_DECLARADO.get(n.declared_type)      # None para 'var' e nomes de classe
        valor=self.infer(n.value)
        if declared and valor and valor in INCOMPATIVEL[declared]:
            self.errors.append(f"Linha {n.line}: tipo incompatível: '{n.name}' é {NOME_TIPO[declared]}, mas recebe um valor do tipo {NOME_TIPO[valor]}")
        self.define(n.name,'var',declared)
    def v_Identifier(self,n):
        if not self.exists(n.name): self.errors.append(f"Linha {n.line}: uso de identificador não declarado '{n.name}'")
    def v_Assignment(self,n):
        self.visit(n.target); self.visit(n.value)
        if isinstance(n.target,Identifier):
            alvo=self.var_type(n.target.name); valor=self.infer(n.value)
            if alvo and valor and valor in INCOMPATIVEL[alvo]:
                self.errors.append(f"Linha {n.line}: tipo incompatível: '{n.target.name}' é {NOME_TIPO[alvo]}, mas recebe um valor do tipo {NOME_TIPO[valor]}")
    def v_FuncDecl(self,n):
        self.enter()
        for p in n.params:self.define(p,'param')
        self.visit(n.body); self.leave()
    def v_ClassDecl(self,n):
        self.enter(); self.define('this','this')
        for m in n.members:self.visit(m)
        self.leave()
    def var_type(self,name):
        """Tipo conhecido de uma variavel ('number','string','bool','list') ou None."""
        for sc,tp in zip(reversed(self.scopes),reversed(self.types)):
            if name in sc: return tp.get(name)
        return None

    def infer(self,e):
        """Tipo de uma expressao quando ele e CERTO; None quando nao da para saber.

        De proposito conservador: so devolve um tipo quando tem certeza, para que
        o semantico nunca acuse erro em um programa correto.
        """
        if isinstance(e,Number): return 'number'
        if isinstance(e,String): return 'string'
        if isinstance(e,Bool): return 'bool'
        if isinstance(e,ListLiteral): return 'list'
        if isinstance(e,Input): return 'number'
        if isinstance(e,Identifier): return self.var_type(e.name)
        if isinstance(e,Unary): return 'bool' if e.op=='!' else ('number' if e.op=='-' else None)
        if isinstance(e,Binary):
            if e.op in ('-','*','/','%'): return 'number'
            if e.op in ('==','!=','<','>','<=','>=','&&','||'): return 'bool'
            if e.op=='+': return 'number' if self.infer(e.left)=='number' and self.infer(e.right)=='number' else None
        if isinstance(e,Index): return 'number' if self.infer(e.obj)=='list' else None
        if isinstance(e,Call) and isinstance(e.callee,Identifier):
            nome=e.callee.name
            if any(nome in sc for sc in self.scopes): return None
            if nome in self.functions or nome in FUNCOES_NUMERICAS: return 'number'
            if nome=='input_text': return 'string'
            if nome=='input_list': return 'list'
        return None

    def v_Fork(self,n):
        if n.task_name in self.forks:self.errors.append(f"Linha {n.line}: tarefa fork '{n.task_name}' duplicada")
        self.forks[n.task_name]=n; self.visit(n.target)
        # fork em outro computador tem regras proprias (ver check_remote_fork)
        if n.target_kind=='computer': self.check_remote_fork(n)
        self.visit(n.body)

    def check_remote_fork(self,n):
        """Valida um fork 'on computer(...)'.

        O corpo precisa ser UMA unica chamada a uma funcao do programa, com a
        mesma quantidade de argumentos que a funcao declara. Motivo: o computador
        remoto recebe apenas o nome da funcao e os valores dos argumentos
        (numeros); ele nao recebe variaveis do programa principal.
        """
        stmts=n.body.statements
        if not (len(stmts)==1 and isinstance(stmts[0],Call) and isinstance(stmts[0].callee,Identifier)):
            self.errors.append(f"Linha {n.line}: fork em computer() deve conter apenas uma chamada de funcao, "
                               f"ex.: fork {n.task_name} on computer(\"IP:porta\") {{ minha_funcao(1, 2); }}")
            return
        call=stmts[0]; fn=self.functions.get(call.callee.name)
        if fn is None:
            self.errors.append(f"Linha {call.line}: fork remoto chama '{call.callee.name}', que nao e uma funcao declarada no programa")
        # quando o destino e um literal, ja confere o formato "IP" ou "IP:porta"
        if isinstance(n.target,String) and not re.fullmatch(r'[^:\s]+(:\d{1,5})?',n.target.value):
            self.errors.append(f"Linha {n.line}: destino de computer() invalido '{n.target.value}'; use \"IP\" ou \"IP:porta\"")

    def v_Join(self,n):
        for t in n.tasks:
            if t not in self.forks:self.errors.append(f"Linha {n.line}: join referencia tarefa fork desconhecida '{t}'")
            else: self.joined.add(t)

    def v_Call(self,n):
        # resultado(t): le o valor devolvido por um fork remoto, depois do join.
        # Se o programa declarar uma funcao chamada 'resultado', ela tem prioridade.
        if isinstance(n.callee,Identifier) and n.callee.name=='resultado' and 'resultado' not in self.functions:
            a=n.args[0] if len(n.args)==1 else None
            if not isinstance(a,Identifier): self.errors.append(f"Linha {n.line}: resultado() espera o nome de uma tarefa fork, ex.: resultado(t)")
            elif a.name not in self.forks: self.errors.append(f"Linha {n.line}: resultado referencia tarefa fork desconhecida '{a.name}'")
            elif self.forks[a.name].target_kind!='computer': self.errors.append(f"Linha {n.line}: resultado('{a.name}') so existe para fork em computer(); fork em core() nao devolve valor")
            elif a.name not in self.joined: self.errors.append(f"Linha {n.line}: resultado('{a.name}') usado antes de join({a.name})")
            return
        # chamada de funcao do programa: confere a quantidade de argumentos
        if isinstance(n.callee,Identifier) and n.callee.name in self.functions and not any(n.callee.name in sc for sc in self.scopes):
            fn=self.functions[n.callee.name]
            if len(fn.params)!=len(n.args):
                self.errors.append(f"Linha {n.line}: '{fn.name}' espera {len(fn.params)} argumento(s), mas recebeu {len(n.args)}")
        self.visit(n.callee)
        for x in n.args:self.visit(x)
