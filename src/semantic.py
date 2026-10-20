from __future__ import annotations
from dataclasses import fields, is_dataclass
from .ast_nodes import *

class SemanticError(Exception): pass
class SemanticAnalyzer:
    def __init__(self): self.scopes=[{}]; self.functions={}; self.classes={}; self.forks={}; self.errors=[]
    def enter(self): self.scopes.append({})
    def leave(self): self.scopes.pop()
    def define(self,name,kind='var'):
        if name in self.scopes[-1]: self.errors.append(f"Identificador '{name}' redeclarado no mesmo escopo")
        self.scopes[-1][name]=kind
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
    def v_VarDecl(self,n): self.visit(n.value); self.define(n.name)
    def v_Identifier(self,n):
        if not self.exists(n.name): self.errors.append(f"Linha {n.line}: uso de identificador não declarado '{n.name}'")
    def v_Assignment(self,n): self.visit(n.target); self.visit(n.value)
    def v_FuncDecl(self,n):
        self.enter()
        for p in n.params:self.define(p,'param')
        self.visit(n.body); self.leave()
    def v_ClassDecl(self,n):
        self.enter(); self.define('this','this')
        for m in n.members:self.visit(m)
        self.leave()
    def v_Fork(self,n):
        if n.task_name in self.forks:self.errors.append(f"Linha {n.line}: tarefa fork '{n.task_name}' duplicada")
        self.forks[n.task_name]=n; self.visit(n.target); self.visit(n.body)
    def v_Join(self,n):
        for t in n.tasks:
            if t not in self.forks:self.errors.append(f"Linha {n.line}: join referencia tarefa fork desconhecida '{t}'")
