from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

class TT(Enum):
    ID=auto(); NUMBER=auto(); STRING=auto(); BOOL=auto(); TYPE=auto(); EOF=auto(); UNKNOWN=auto()
    CLASS=auto(); EXTENDS=auto(); NEW=auto(); FUNC=auto(); VAR=auto(); IF=auto(); ELSE=auto(); WHILE=auto(); FOR=auto(); IN=auto(); BREAK=auto(); CONTINUE=auto(); RETURN=auto(); SEQ=auto(); PAR=auto(); THIS=auto()
    C_CHANNEL=auto(); SEND=auto(); RECEIVE=auto(); INPUT=auto(); PRINT=auto(); FORK=auto(); JOIN=auto(); ON=auto(); CORE=auto(); COMPUTER=auto(); AS=auto()
    PLUS=auto(); MINUS=auto(); STAR=auto(); SLASH=auto(); MOD=auto(); ASSIGN=auto(); EQ=auto(); NEQ=auto(); NOT=auto(); AND=auto(); OR=auto(); LT=auto(); GT=auto(); LTE=auto(); GTE=auto()
    LP=auto(); RP=auto(); LB=auto(); RB=auto(); LS=auto(); RS=auto(); DOT=auto(); SEMI=auto(); COMMA=auto(); COLON=auto()

KEYWORDS={
'class':TT.CLASS,'extends':TT.EXTENDS,'new':TT.NEW,'func':TT.FUNC,'var':TT.VAR,'if':TT.IF,'else':TT.ELSE,'while':TT.WHILE,'for':TT.FOR,'in':TT.IN,'break':TT.BREAK,'continue':TT.CONTINUE,'return':TT.RETURN,'seq':TT.SEQ,'SEQ':TT.SEQ,'par':TT.PAR,'PAR':TT.PAR,'this':TT.THIS,
'c_channel':TT.C_CHANNEL,'send':TT.SEND,'receive':TT.RECEIVE,'input':TT.INPUT,'print':TT.PRINT,'fork':TT.FORK,'Fork':TT.FORK,'join':TT.JOIN,'Join':TT.JOIN,'on':TT.ON,'core':TT.CORE,'computer':TT.COMPUTER,'as':TT.AS,
'true':TT.BOOL,'false':TT.BOOL,'number':TT.TYPE,'int':TT.TYPE,'float':TT.TYPE,'string':TT.TYPE,'bool':TT.TYPE,'void':TT.TYPE,'list':TT.TYPE,'dict':TT.TYPE
}
@dataclass
class Token:
    type:TT; lexeme:str; line:int; col:int

class LexerError(Exception): pass
class Lexer:
    def __init__(self, source:str): self.s=source; self.i=0; self.line=1; self.col=1
    def peek(self,n=0):
        j=self.i+n; return self.s[j] if j<len(self.s) else '\0'
    def adv(self):
        c=self.peek(); self.i+=1
        if c=='\n': self.line+=1; self.col=1
        else: self.col+=1
        return c
    def tokenize(self):
        out=[]
        while self.i<len(self.s):
            c=self.peek()
            if c.isspace(): self.adv(); continue
            if c=='#':
                while self.peek() not in ('\n','\0'): self.adv()
                continue
            l,co=self.line,self.col
            if c.isalpha() or c=='_':
                x=''
                while self.peek().isalnum() or self.peek()=='_': x+=self.adv()
                out.append(Token(KEYWORDS.get(x,TT.ID),x,l,co)); continue
            if c.isdigit():
                x=''
                while self.peek().isdigit(): x+=self.adv()
                if self.peek()=='.':
                    x+=self.adv()
                    while self.peek().isdigit(): x+=self.adv()
                out.append(Token(TT.NUMBER,x,l,co)); continue
            if c=='"':
                self.adv(); x=''
                while self.peek() not in ('"','\0'):
                    if self.peek()=='\\':
                        self.adv(); e=self.adv(); x += {'n':'\n','t':'\t','"':'"','\\':'\\'}.get(e,e)
                    else: x+=self.adv()
                if self.peek()!='"': raise LexerError(f'Linha {l}:{co}: string não terminada')
                self.adv(); out.append(Token(TT.STRING,x,l,co)); continue
            two=c+self.peek(1)
            tm={'==':TT.EQ,'!=':TT.NEQ,'<=':TT.LTE,'>=':TT.GTE,'&&':TT.AND,'||':TT.OR}
            if two in tm: self.adv(); self.adv(); out.append(Token(tm[two],two,l,co)); continue
            sm={'+':TT.PLUS,'-':TT.MINUS,'*':TT.STAR,'/':TT.SLASH,'%':TT.MOD,'=':TT.ASSIGN,'!':TT.NOT,'<':TT.LT,'>':TT.GT,'(':TT.LP,')':TT.RP,'{':TT.LB,'}':TT.RB,'[':TT.LS,']':TT.RS,'.':TT.DOT,';':TT.SEMI,',':TT.COMMA,':':TT.COLON}
            if c in sm: self.adv(); out.append(Token(sm[c],c,l,co)); continue
            raise LexerError(f'Linha {l}:{co}: caractere inválido {c!r}')
        out.append(Token(TT.EOF,'',self.line,self.col)); return out
