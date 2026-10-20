from src.compiler import compile_source

def test_basico_pipeline():
    src='seq { int x = 2; int y = 3; print("soma=", x + y); }'
    r=compile_source(src,build=False)
    assert not r['semantic_errors']
    assert any(t['type']=='SEQ' for t in r['tokens'])
    assert 'PRINT' in r['tac']
    assert 'int main()' in r['cpp']

def test_fork_join_ast():
    src='seq { fork a on core(1) { print("A"); } fork b on core(2) { print("B"); } join(a,b); }'
    r=compile_source(src,build=False)
    assert not r['semantic_errors']
    assert 'FORK a' in r['tac'] and 'JOIN a, b' in r['tac']
    assert 'std::thread __fork_a' in r['cpp']

def test_join_invalido():
    r=compile_source('seq { join(x); }',build=False)
    assert any('desconhecida' in e for e in r['semantic_errors'])
