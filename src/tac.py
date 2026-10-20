from __future__ import annotations
from .ast_nodes import *
class TACGenerator:
    def __init__(self): self.out=[]; self.temp=0; self.label=0
    def t(self): self.temp+=1; return f't{self.temp}'
    def l(self,p='L'): self.label+=1; return f'{p}{self.label}'
    def generate(self,n): self.emit_node(n); return '\n'.join(self.out)
    def emit_node(self,n):
        if n is None:return None
        if isinstance(n,Program):
            for s in n.statements:self.emit_node(s)
        elif isinstance(n,Block):
            self.out.append(f'# {n.kind.upper()} BEGIN')
            for s in n.statements:self.emit_node(s)
            self.out.append(f'# {n.kind.upper()} END')
        elif isinstance(n,VarDecl): self.out.append(f'{n.name} = {self.expr(n.value) if n.value else "0"}')
        elif isinstance(n,Assignment): self.out.append(f'{self.expr(n.target)} = {self.expr(n.value)}')
        elif isinstance(n,Print): self.out.append('PRINT '+', '.join(self.expr(x) for x in n.args))
        elif isinstance(n,Return): self.out.append('RETURN '+(self.expr(n.value) if n.value else ''))
        elif isinstance(n,If):
            le=self.l('ELSE'); lend=self.l('ENDIF'); c=self.expr(n.cond); self.out.append(f'IF_FALSE {c} GOTO {le}'); self.emit_node(n.then_branch); self.out.append(f'GOTO {lend}'); self.out.append(le+':'); self.emit_node(n.else_branch); self.out.append(lend+':')
        elif isinstance(n,While):
            a=self.l('WHILE'); b=self.l('ENDWHILE'); self.out.append(a+':'); c=self.expr(n.cond); self.out.append(f'IF_FALSE {c} GOTO {b}'); self.emit_node(n.body); self.out.append(f'GOTO {a}'); self.out.append(b+':')
        elif isinstance(n,For):
            self.emit_node(n.init); a=self.l('FOR'); b=self.l('ENDFOR'); self.out.append(a+':');
            if n.cond:self.out.append(f'IF_FALSE {self.expr(n.cond)} GOTO {b}')
            self.emit_node(n.body); self.emit_node(n.inc); self.out.append(f'GOTO {a}'); self.out.append(b+':')
        elif isinstance(n,FuncDecl): self.out.append(f'FUNC {n.name}({", ".join(n.params)}):'); self.emit_node(n.body); self.out.append('END_FUNC')
        elif isinstance(n,ClassDecl): self.out.append(f'CLASS {n.name}'); [self.emit_node(x) for x in n.members]; self.out.append('END_CLASS')
        elif isinstance(n,Send): self.out.append('SEND '+self.expr(n.channel)+', '+', '.join(self.expr(x) for x in n.payload))
        elif isinstance(n,Fork): self.out.append(f'FORK {n.task_name} ON {n.target_kind}({self.expr(n.target)})'); self.emit_node(n.body); self.out.append(f'END_FORK {n.task_name}')
        elif isinstance(n,Join): self.out.append('JOIN '+', '.join(n.tasks))
        elif isinstance(n,(Call,Property,Identifier,Number,String,Bool,Binary,Unary,New,Channel,Receive,Input,ListLiteral,Index)): self.out.append(self.expr(n))
    def expr(self,n):
        if n is None:return 'null'
        if isinstance(n,Identifier):return n.name
        if isinstance(n,Number):return n.value
        if isinstance(n,String):return repr(n.value)
        if isinstance(n,Bool):return 'true' if n.value else 'false'
        if isinstance(n,Binary):
            a=self.expr(n.left); b=self.expr(n.right); t=self.t(); self.out.append(f'{t} = {a} {n.op} {b}'); return t
        if isinstance(n,Unary):
            a=self.expr(n.expr); t=self.t(); self.out.append(f'{t} = {n.op}{a}'); return t
        if isinstance(n,Property):return self.expr(n.obj)+'.'+n.name
        if isinstance(n,Call):
            t=self.t(); self.out.append(f'{t} = CALL {self.expr(n.callee)}({", ".join(self.expr(x) for x in n.args)})'); return t
        if isinstance(n,New):return f'NEW {n.class_name}({", ".join(self.expr(x) for x in n.args)})'
        if isinstance(n,Channel):return f'C_CHANNEL({self.expr(n.host)}, {self.expr(n.port)})'
        if isinstance(n,Receive):return f'RECEIVE({self.expr(n.channel)})'
        if isinstance(n,Input):return f'INPUT({self.expr(n.prompt) if n.prompt else ""})'
        if isinstance(n,ListLiteral):return '['+', '.join(self.expr(x) for x in n.items)+']'
        if isinstance(n,Index):return f'{self.expr(n.obj)}[{self.expr(n.index)}]'
        return n.__class__.__name__
