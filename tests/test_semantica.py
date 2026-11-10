"""Testes da analise semantica: tipos, numero de argumentos e ausencia de falsos erros."""
import glob, os
import pytest
from src.compiler import compile_source

def erros(src): return compile_source(src, build=False)['semantic_errors']
SOMA = 'func soma(a, b) { return a + b; }\n'

@pytest.mark.parametrize('src,trecho', [
    ('seq { number x = "abc"; }', 'tipo incompatível'),
    ('seq { string s = 5; }', 'tipo incompatível'),
    ('seq { list l = 3; }', 'tipo incompatível'),
    ('seq { number x = 1; x = "oi"; }', 'tipo incompatível'),
    (SOMA + 'seq { print(soma(1)); }', 'espera 2 argumento'),
    (SOMA + 'seq { print(soma(1, 2, 3)); }', 'espera 2 argumento'),
])
def test_erros_detectados(src, trecho):
    assert any(trecho in e for e in erros(src))

@pytest.mark.parametrize('src', [
    'seq { number x = 3 > 2; bool b = 1; }',                 # number/bool se misturam
    'seq { var x = 5; x = "oi"; }',                          # var nao tem tipo fixo
    SOMA + 'seq { number r = soma(1, 2); list l = [1, 2]; number e = l[0] + 1; string t = "a"; }',
])
def test_programas_validos_sem_erro(src):
    assert not erros(src)

def test_nenhum_programa_do_projeto_gera_erro_semantico():
    """Guarda contra falsos positivos: todo .minipar de tests/ deve passar limpo."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    arquivos = glob.glob(os.path.join(raiz, 'tests', '*.minipar'))
    assert len(arquivos) >= 13
    for f in arquivos:
        assert not erros(open(f, encoding='utf-8').read()), os.path.basename(f)
