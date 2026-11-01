"""Testes do fork remoto: fork t on computer("IP:porta") { f(...); } + resultado(t)."""
import os, shutil, socket, subprocess, time
import pytest
from src.compiler import compile_source

FUNC = 'func f(a, b) { return a + b; }\n'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def erros(corpo):
    return compile_source(FUNC + 'seq {\n' + corpo + '\n}', build=False)['semantic_errors']

# ---------- analise semantica (nao precisa de g++) ----------
def test_fork_remoto_valido():
    assert not erros('fork t on computer("127.0.0.1:6000") { f(1, 2); }\njoin(t);\nnumber r = resultado(t);\nprint(r);')

def test_corpo_deve_ser_chamada_de_funcao():
    assert any('apenas uma chamada' in e for e in erros('fork t on computer("127.0.0.1:6000") { print("oi"); }\njoin(t);'))

def test_funcao_inexistente():
    assert any('naoexiste' in e for e in erros('fork t on computer("127.0.0.1:6000") { naoexiste(1); }\njoin(t);'))

def test_aridade_errada():
    assert any('espera 2 argumento' in e for e in erros('fork t on computer("127.0.0.1:6000") { f(1); }\njoin(t);'))

def test_destino_invalido():
    assert any('destino' in e for e in erros('fork t on computer("a b:c") { f(1, 2); }\njoin(t);'))

def test_resultado_antes_do_join():
    assert any('antes de join' in e for e in erros('fork t on computer("127.0.0.1:6000") { f(1, 2); }\nnumber r = resultado(t);\njoin(t);'))

def test_resultado_de_fork_em_core():
    assert any('so existe para fork em computer' in e for e in erros('fork t on core(1) { f(1, 2); }\njoin(t);\nnumber r = resultado(t);'))

def test_resultado_de_tarefa_inexistente():
    assert any('desconhecida' in e for e in erros('number r = resultado(x);'))

# ---------- execucao de ponta a ponta (precisa de g++) ----------
precisa_gpp = pytest.mark.skipif(shutil.which('g++') is None, reason='g++ nao encontrado')

def _porta_livre():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0)); return s.getsockname()[1]

def _compilar(tmp_path, porta):
    src = open(os.path.join(ROOT, 'tests', 'teste11_fork_remoto.minipar'), encoding='utf-8').read().replace('6000', str(porta))
    r = compile_source(src, str(tmp_path / 'prog'), True)
    assert not r['semantic_errors'] and r['build']['ok'], r
    return r['build']['exe']

@precisa_gpp
def test_fork_remoto_com_worker(tmp_path):
    porta = _porta_livre(); exe = _compilar(tmp_path, porta)
    worker = subprocess.Popen([exe, '--worker', str(porta)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):                      # espera o worker abrir a porta
            try: socket.create_connection(('127.0.0.1', porta), timeout=0.2).close(); break
            except OSError: time.sleep(0.1)
        r = subprocess.run([exe], capture_output=True, text=True, timeout=60)
    finally:
        worker.kill(); worker.wait()
    assert r.returncode == 0, r.stderr
    assert 'OK: resultados remotos identicos' in r.stdout

@precisa_gpp
def test_fork_remoto_sem_worker_da_erro_claro(tmp_path):
    exe = _compilar(tmp_path, _porta_livre())    # ninguem escutando nessa porta
    r = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    assert r.returncode != 0
    assert 'nao foi possivel conectar' in r.stderr
