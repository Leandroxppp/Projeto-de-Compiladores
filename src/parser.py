from __future__ import annotations
from .lexer import TT, Token
from .ast_nodes import *

class ParseError(Exception): pass
class Parser:
    def __init__(self,tokens:list[Token]): self.t=tokens; self.i=0
    def p(self): return self.t[min(self.i,len(self.t)-1)]
    def a(self): x=self.p(); self.i+=1; return x
    def m(self,*types):
        if self.p().type in types: return self.a()
    def c(self,typ,msg):
        if self.p().type==typ: return self.a()
        x=self.p(); raise ParseError(f'Linha {x.line}:{x.col}: {msg}; encontrado {x.lexeme!r}')
    def parse(self):
        ss=[]
        while self.p().type!=TT.EOF: ss.append(self.statement())
        return Program(ss)
    def block(self,kind='seq'):
        self.c(TT.LB,"esperado '{'"); ss=[]
        while self.p().type not in (TT.RB,TT.EOF): ss.append(self.statement())
        self.c(TT.RB,"esperado '}'"); return Block(ss,kind)
    def statement(self):
        tok=self.p()
        if self.m(TT.SEQ): return self.block('seq')
        if self.m(TT.PAR): return self.block('par')
        if self.m(TT.LB):
            self.i-=1; return self.block('seq')
        if self.m(TT.VAR): return self.var_decl('var',tok.line)
        if self.p().type==TT.TYPE: return self.var_decl(self.a().lexeme,tok.line)
        if self.m(TT.PRINT): return self.print_stmt(tok.line)
        if self.m(TT.IF): return self.if_stmt(tok.line)
        if self.m(TT.WHILE): return self.while_stmt(tok.line)
        if self.m(TT.FOR): return self.for_stmt(tok.line)
        if self.m(TT.FUNC): return self.func_decl(tok.line)
        if self.m(TT.CLASS): return self.class_decl(tok.line)
        if self.m(TT.RETURN):
            v=None if self.p().type==TT.SEMI else self.expr(); self.m(TT.SEMI); return Return(v,tok.line)
        if self.m(TT.BREAK): self.m(TT.SEMI); return Break(tok.line)
        if self.m(TT.CONTINUE): self.m(TT.SEMI); return Continue(tok.line)
        if self.m(TT.SEND): return self.send_stmt(tok.line)
        if self.m(TT.FORK): return self.fork_stmt(tok.line)
        if self.m(TT.JOIN): return self.join_stmt(tok.line)
        e=self.expr()
        if self.m(TT.ASSIGN):
            v=self.expr(); self.c(TT.SEMI,"esperado ';'"); return Assignment(e,v,tok.line)
        self.c(TT.SEMI,"esperado ';'"); return e
    def var_decl(self,typ,line):
        name=self.c(TT.ID,'esperado nome da variável').lexeme; v=None
        if self.m(TT.ASSIGN): v=self.expr()
        self.c(TT.SEMI,"esperado ';'"); return VarDecl(name,v,typ,line)
    def print_stmt(self,line):
        self.c(TT.LP,"esperado '('"); args=[]
        if self.p().type!=TT.RP:
            args.append(self.expr())
            while self.m(TT.COMMA): args.append(self.expr())
        self.c(TT.RP,"esperado ')'"); self.c(TT.SEMI,"esperado ';'"); return Print(args,line)
    def if_stmt(self,line):
        self.c(TT.LP,"esperado '('"); cond=self.expr(); self.c(TT.RP,"esperado ')'"); t=self.statement(); e=self.statement() if self.m(TT.ELSE) else None; return If(cond,t,e,line)
    def while_stmt(self,line):
        self.c(TT.LP,"esperado '('"); cond=self.expr(); self.c(TT.RP,"esperado ')'"); return While(cond,self.statement(),line)
    def for_stmt(self,line):
        self.c(TT.LP,"esperado '('"); init=cond=inc=None
        if self.m(TT.VAR): init=self.var_decl('var',line)
        elif self.p().type==TT.TYPE: init=self.var_decl(self.a().lexeme,line)
        elif self.m(TT.SEMI): pass
        else:
            e=self.expr();
            if self.m(TT.ASSIGN): init=Assignment(e,self.expr(),line)
            else: init=e
            self.c(TT.SEMI,"esperado ';'")
        if self.p().type!=TT.SEMI: cond=self.expr()
        self.c(TT.SEMI,"esperado ';'")
        if self.p().type!=TT.RP:
            e=self.expr(); inc=Assignment(e,self.expr(),line) if self.m(TT.ASSIGN) else e
        self.c(TT.RP,"esperado ')'"); return For(init,cond,inc,self.statement(),line)
    def func_decl(self,line):
        name=self.c(TT.ID,'esperado nome da função').lexeme; self.c(TT.LP,"esperado '('"); ps=[]
        if self.p().type!=TT.RP:
            if self.p().type==TT.TYPE: self.a()
            ps.append(self.c(TT.ID,'esperado parâmetro').lexeme)
            while self.m(TT.COMMA):
                if self.p().type==TT.TYPE:self.a()
                ps.append(self.c(TT.ID,'esperado parâmetro').lexeme)
        self.c(TT.RP,"esperado ')'"); return FuncDecl(name,ps,self.block('seq'),line)
    def class_decl(self,line):
        name=self.c(TT.ID,'esperado nome da classe').lexeme; sup=self.c(TT.ID,'esperado superclasse').lexeme if self.m(TT.EXTENDS) else None
        self.c(TT.LB,"esperado '{'"); mem=[]
        while self.p().type not in (TT.RB,TT.EOF):
            if self.m(TT.VAR): mem.append(self.var_decl('var',self.p().line))
            elif self.p().type==TT.TYPE: mem.append(self.var_decl(self.a().lexeme,self.p().line))
            elif self.m(TT.FUNC): mem.append(self.func_decl(self.p().line))
            else: raise ParseError(f'Linha {self.p().line}: membro de classe deve ser var/tipo/func')
        self.c(TT.RB,"esperado '}'"); return ClassDecl(name,sup,mem,line)
    def send_stmt(self,line):
        self.c(TT.LP,"esperado '('"); ch=self.expr(); payload=[]
        while self.m(TT.COMMA): payload.append(self.expr())
        self.c(TT.RP,"esperado ')'"); self.c(TT.SEMI,"esperado ';'"); return Send(ch,payload,line)
    def fork_stmt(self,line):
        name=self.c(TT.ID,'esperado nome da subtarefa').lexeme
        self.c(TT.ON,"esperado 'on'")
        if self.m(TT.CORE): kind='core'; self.c(TT.LP,"esperado '('"); target=self.expr(); self.c(TT.RP,"esperado ')'")
        elif self.m(TT.COMPUTER): kind='computer'; self.c(TT.LP,"esperado '('"); target=self.expr(); self.c(TT.RP,"esperado ')'")
        else: raise ParseError(f"Linha {self.p().line}: esperado core(...) ou computer(...)")
        body=self.block('fork'); self.m(TT.SEMI); return Fork(name,kind,target,body,line)
    def join_stmt(self,line):
        tasks=[]
        if self.m(TT.LP):
            tasks.append(self.c(TT.ID,'esperado tarefa').lexeme)
            while self.m(TT.COMMA): tasks.append(self.c(TT.ID,'esperado tarefa').lexeme)
            self.c(TT.RP,"esperado ')'")
        else:
            tasks.append(self.c(TT.ID,'esperado tarefa').lexeme)
            while self.m(TT.COMMA): tasks.append(self.c(TT.ID,'esperado tarefa').lexeme)
        self.c(TT.SEMI,"esperado ';'"); return Join(tasks,line)
    def expr(self): return self.or_()
    def or_(self):
        e=self.and_()
        while (o:=self.m(TT.OR)): e=Binary(o.lexeme,e,self.and_(),o.line)
        return e
    def and_(self):
        e=self.eq()
        while (o:=self.m(TT.AND)): e=Binary(o.lexeme,e,self.eq(),o.line)
        return e
    def eq(self):
        e=self.comp()
        while self.p().type in (TT.EQ,TT.NEQ): o=self.a(); e=Binary(o.lexeme,e,self.comp(),o.line)
        return e
    def comp(self):
        e=self.term()
        while self.p().type in (TT.LT,TT.LTE,TT.GT,TT.GTE): o=self.a(); e=Binary(o.lexeme,e,self.term(),o.line)
        return e
    def term(self):
        e=self.factor()
        while self.p().type in (TT.PLUS,TT.MINUS): o=self.a(); e=Binary(o.lexeme,e,self.factor(),o.line)
        return e
    def factor(self):
        e=self.unary()
        while self.p().type in (TT.STAR,TT.SLASH,TT.MOD): o=self.a(); e=Binary(o.lexeme,e,self.unary(),o.line)
        return e
    def unary(self):
        if self.p().type in (TT.NOT,TT.MINUS): o=self.a(); return Unary(o.lexeme,self.unary(),o.line)
        return self.postfix()
    def postfix(self):
        e=self.primary()
        while True:
            if self.m(TT.LP):
                args=[]
                if self.p().type!=TT.RP:
                    args.append(self.expr())
                    while self.m(TT.COMMA): args.append(self.expr())
                self.c(TT.RP,"esperado ')'"); e=Call(e,args,getattr(e,'line',1))
            elif self.m(TT.DOT): e=Property(e,self.c(TT.ID,'esperado propriedade/método').lexeme,getattr(e,'line',1))
            elif self.m(TT.LS): idx=self.expr(); self.c(TT.RS,"esperado ']'"); e=Index(e,idx,getattr(e,'line',1))
            else: break
        return e
    def primary(self):
        t=self.a()
        if t.type==TT.NUMBER:return Number(t.lexeme,t.line)
        if t.type==TT.STRING:return String(t.lexeme,t.line)
        if t.type==TT.BOOL:return Bool(t.lexeme=='true',t.line)
        if t.type==TT.ID:return Identifier(t.lexeme,t.line)
        if t.type==TT.THIS:return This(t.line)
        if t.type==TT.NEW:
            n=self.c(TT.ID,'esperado classe').lexeme; self.c(TT.LP,"esperado '('"); args=[]
            if self.p().type!=TT.RP:
                args.append(self.expr())
                while self.m(TT.COMMA):args.append(self.expr())
            self.c(TT.RP,"esperado ')'"); return New(n,args,t.line)
        if t.type==TT.C_CHANNEL:
            self.c(TT.LP,"esperado '('"); h=self.expr(); self.c(TT.COMMA,"esperado ','"); p=self.expr(); self.c(TT.RP,"esperado ')'"); return Channel(h,p,t.line)
        if t.type==TT.RECEIVE:
            self.c(TT.LP,"esperado '('"); c=self.expr(); self.c(TT.RP,"esperado ')'"); return Receive(c,t.line)
        if t.type==TT.INPUT:
            self.c(TT.LP,"esperado '('"); p=None if self.p().type==TT.RP else self.expr(); self.c(TT.RP,"esperado ')'"); return Input(p,t.line)
        if t.type==TT.LS:
            xs=[]
            if self.p().type!=TT.RS:
                xs.append(self.expr())
                while self.m(TT.COMMA):xs.append(self.expr())
            self.c(TT.RS,"esperado ']'"); return ListLiteral(xs,t.line)
        if t.type==TT.LP:
            e=self.expr(); self.c(TT.RP,"esperado ')'"); return e
        raise ParseError(f'Linha {t.line}:{t.col}: expressão inesperada {t.lexeme!r}')
