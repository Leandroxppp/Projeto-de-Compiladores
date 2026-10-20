from __future__ import annotations
import json, os, subprocess
from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticAnalyzer
from .tac import TACGenerator
from .codegen import CppCodeGenerator, compile_cpp

def ast_to_dict(node): return node.to_dict()
def compile_source(source:str,out_base:str|None=None,build=True):
    tokens=Lexer(source).tokenize(); ast=Parser(tokens).parse(); sem=SemanticAnalyzer(); errors=sem.analyze(ast)
    tac=TACGenerator().generate(ast); cpp=CppCodeGenerator().generate(ast)
    result={'tokens':[{'type':t.type.name,'lexeme':t.lexeme,'line':t.line,'col':t.col} for t in tokens], 'ast':ast_to_dict(ast), 'semantic_errors':errors, 'tac':tac, 'cpp':cpp}
    if build and out_base and not errors: result['build']=compile_cpp(cpp,out_base)
    return result

def execute(exe,timeout=15):
    p=subprocess.run([exe],capture_output=True,text=True,timeout=timeout)
    return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
