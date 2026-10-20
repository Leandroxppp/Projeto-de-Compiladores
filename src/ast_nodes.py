from __future__ import annotations
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import Any, Optional

class ASTNode:
    line: int = 1
    def to_dict(self):
        def conv(v):
            if is_dataclass(v):
                d = {"node": v.__class__.__name__}
                for k, val in asdict(v).items(): d[k] = conv(val)
                return d
            if isinstance(v, list): return [conv(x) for x in v]
            return v
        return conv(self)

@dataclass
class Program(ASTNode):
    statements: list[ASTNode] = field(default_factory=list); line:int=1
@dataclass
class Block(ASTNode):
    statements:list[ASTNode]=field(default_factory=list); kind:str="seq"; line:int=1
@dataclass
class VarDecl(ASTNode):
    name:str=""; value:Optional[ASTNode]=None; declared_type:str="var"; line:int=1
@dataclass
class Assignment(ASTNode):
    target:ASTNode=None; value:ASTNode=None; line:int=1
@dataclass
class Identifier(ASTNode):
    name:str=""; line:int=1
@dataclass
class Number(ASTNode):
    value:str="0"; line:int=1
@dataclass
class String(ASTNode):
    value:str=""; line:int=1
@dataclass
class Bool(ASTNode):
    value:bool=False; line:int=1
@dataclass
class Binary(ASTNode):
    op:str=""; left:ASTNode=None; right:ASTNode=None; line:int=1
@dataclass
class Unary(ASTNode):
    op:str=""; expr:ASTNode=None; line:int=1
@dataclass
class Print(ASTNode):
    args:list[ASTNode]=field(default_factory=list); line:int=1
@dataclass
class If(ASTNode):
    cond:ASTNode=None; then_branch:ASTNode=None; else_branch:Optional[ASTNode]=None; line:int=1
@dataclass
class While(ASTNode):
    cond:ASTNode=None; body:ASTNode=None; line:int=1
@dataclass
class For(ASTNode):
    init:Optional[ASTNode]=None; cond:Optional[ASTNode]=None; inc:Optional[ASTNode]=None; body:ASTNode=None; line:int=1
@dataclass
class FuncDecl(ASTNode):
    name:str=""; params:list[str]=field(default_factory=list); body:Block=None; line:int=1
@dataclass
class Return(ASTNode):
    value:Optional[ASTNode]=None; line:int=1
@dataclass
class Call(ASTNode):
    callee:ASTNode=None; args:list[ASTNode]=field(default_factory=list); line:int=1
@dataclass
class Property(ASTNode):
    obj:ASTNode=None; name:str=""; line:int=1
@dataclass
class ClassDecl(ASTNode):
    name:str=""; superclass:Optional[str]=None; members:list[ASTNode]=field(default_factory=list); line:int=1
@dataclass
class New(ASTNode):
    class_name:str=""; args:list[ASTNode]=field(default_factory=list); line:int=1
@dataclass
class This(ASTNode):
    line:int=1
@dataclass
class ListLiteral(ASTNode):
    items:list[ASTNode]=field(default_factory=list); line:int=1
@dataclass
class Index(ASTNode):
    obj:ASTNode=None; index:ASTNode=None; line:int=1
@dataclass
class Channel(ASTNode):
    host:ASTNode=None; port:ASTNode=None; line:int=1
@dataclass
class Send(ASTNode):
    channel:ASTNode=None; payload:list[ASTNode]=field(default_factory=list); line:int=1
@dataclass
class Receive(ASTNode):
    channel:ASTNode=None; line:int=1
@dataclass
class Input(ASTNode):
    prompt:Optional[ASTNode]=None; line:int=1
@dataclass
class Fork(ASTNode):
    task_name:str=""; target_kind:str="core"; target:ASTNode=None; body:Block=None; line:int=1
@dataclass
class Join(ASTNode):
    tasks:list[str]=field(default_factory=list); line:int=1
@dataclass
class Break(ASTNode): line:int=1
@dataclass
class Continue(ASTNode): line:int=1
