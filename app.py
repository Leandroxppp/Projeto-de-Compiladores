from flask import Flask, render_template, request, jsonify, send_file
import os
import re
import subprocess
import time
import uuid
from src.compiler import compile_source, execute

app = Flask(__name__)
ROOT = os.path.dirname(__file__)
OUT = os.path.join(ROOT, 'output')
TESTS = os.path.join(ROOT, 'tests')
os.makedirs(OUT, exist_ok=True)

EXAMPLE = '''# MiniPar 2026.2\nseq {\n  int x = 6;\n  int y = 7;\n  print("Resultado = ", x * y);\n}\n'''

TEST_LABELS = {
    'teste1_calculadora_cliente.minipar': 'Teste 1A — Calculadora (cliente)',
    'teste1_calculadora_servidor.minipar': 'Teste 1B — Calculadora (servidor)',
    'teste2_fatorial_fibonacci_par.minipar': 'Teste 2 — Fatorial + Fibonacci em PAR',
    'teste3_neuronio_oo.minipar': 'Teste 3 — Neurônio com OO',
    'teste4_xor.minipar': 'Teste 4 — Rede XOR',
    'teste5_recomendacao.minipar': 'Teste 5 — Recomendação',
    'teste6_ordenacao_lista.minipar': 'Teste 6 — Ordenação de lista',
    'teste7_quicksort_oo.minipar': 'Teste 7 — Quicksort iterativo',
    'teste8_avaliacao_4_nucleos.minipar': 'Teste 8 — Avaliação em 4 núcleos',
    'teste9_5_nucleos_fractal.minipar': 'Teste 9 — 5 núcleos + Mandelbrot',
    'teste10_6_nucleos_2_fractais.minipar': 'Teste 10 — 6 núcleos + 2 fractais',
    'teste_basico.minipar': 'Exemplo básico — SEQ/PAR',
}


def available_tests():
    if not os.path.isdir(TESTS):
        return []
    names = [n for n in os.listdir(TESTS) if n.endswith('.minipar') and os.path.isfile(os.path.join(TESTS, n))]
    return [{'file': n, 'label': TEST_LABELS.get(n, n)} for n in sorted(names, key=lambda x: (x == 'teste_basico.minipar', x))]


def _web_executable(ident):
    if not re.fullmatch(r'[0-9a-f]{10}', ident or ''):
        return None
    return os.path.join(OUT, 'web_' + ident + ('.exe' if os.name == 'nt' else ''))


def _read_test(name):
    path = os.path.join(TESTS, name)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


@app.get('/')
def home():
    return render_template('index.html', example=EXAMPLE)


@app.get('/dev')
def dev():
    return render_template('dev.html', example=EXAMPLE, tests=available_tests())


@app.get('/learn')
def learn():
    return render_template('learn.html', example=EXAMPLE, tests=available_tests())


@app.get('/api/tests/<path:filename>')
def load_test(filename):
    safe_name = os.path.basename(filename)
    if safe_name != filename or not safe_name.endswith('.minipar'):
        return jsonify({'ok': False, 'error': 'Nome de teste inválido'}), 400
    path = os.path.join(TESTS, safe_name)
    if not os.path.isfile(path):
        return jsonify({'ok': False, 'error': 'Teste não encontrado'}), 404
    with open(path, 'r', encoding='utf-8') as f:
        code = f.read()
    return jsonify({'ok': True, 'file': safe_name, 'label': TEST_LABELS.get(safe_name, safe_name), 'code': code})


@app.post('/api/analyze')
def analyze():
    data = request.get_json(silent=True) or {}
    code = data.get('code', '')
    try:
        r = compile_source(code, build=False)
        return jsonify({'ok': True, **r})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.post('/api/compile')
def compile_api():
    data = request.get_json(silent=True) or {}
    code = data.get('code', '')
    ident = uuid.uuid4().hex[:10]
    base = os.path.join(OUT, 'web_' + ident)
    try:
        r = compile_source(code, base, True)
        r['id'] = ident
        if r.get('build', {}).get('ok'):
            r['download'] = '/api/download/' + ident
        return jsonify({'ok': not r.get('semantic_errors') and r.get('build', {}).get('ok', False), **r})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.post('/api/run')
def run_api():
    data = request.get_json(silent=True) or {}
    ident = data.get('id', '')
    stdin_text = data.get('stdin', '')
    path = _web_executable(ident)
    if not path or not os.path.exists(path):
        return jsonify({'ok': False, 'error': 'Executável não encontrado'}), 404
    try:
        result = execute(path, timeout=15, stdin_text=stdin_text)
        return jsonify({'ok': True, **result})
    except subprocess.TimeoutExpired:
        return jsonify({
            'ok': False,
            'error': 'Tempo limite de 15 s excedido. O programa pode estar aguardando entrada, conexão ou outro processo.'
        }), 408
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.post('/api/run-test1')
def run_test1():
    """Compila e executa cliente + servidor do Teste 1 em localhost."""
    data = request.get_json(silent=True) or {}
    try:
        operation = int(data.get('operation', 1))
        value1 = float(data.get('value1', 10))
        value2 = float(data.get('value2', 5))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Operandos inválidos.'}), 400

    if operation not in (1, 2, 3, 4):
        return jsonify({'ok': False, 'error': 'Operação deve ser 1, 2, 3 ou 4.'}), 400

    run_id = uuid.uuid4().hex[:10]
    server_base = os.path.join(OUT, 'web_calc_server_' + run_id)
    client_base = os.path.join(OUT, 'web_calc_client_' + run_id)

    server = None
    try:
        server_result = compile_source(_read_test('teste1_calculadora_servidor.minipar'), server_base, True)
        client_result = compile_source(_read_test('teste1_calculadora_cliente.minipar'), client_base, True)

        if not server_result.get('build', {}).get('ok'):
            return jsonify({'ok': False, 'error': 'Falha ao compilar o servidor.', 'details': server_result.get('build', {}).get('stderr', '')}), 400
        if not client_result.get('build', {}).get('ok'):
            return jsonify({'ok': False, 'error': 'Falha ao compilar o cliente.', 'details': client_result.get('build', {}).get('stderr', '')}), 400

        server_exe = server_result['build']['exe']
        client_exe = client_result['build']['exe']
        server = subprocess.Popen(
            [server_exe],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(0.45)

        client_input = f'127.0.0.1\n{operation}\n{value1}\n{value2}\n'
        client_proc = subprocess.run(
            [client_exe],
            input=client_input,
            capture_output=True,
            text=True,
            timeout=10,
        )
        server_stdout, server_stderr = server.communicate(timeout=10)

        ok = client_proc.returncode == 0 and server.returncode == 0
        return jsonify({
            'ok': ok,
            'client_stdout': client_proc.stdout,
            'client_stderr': client_proc.stderr,
            'client_returncode': client_proc.returncode,
            'server_stdout': server_stdout,
            'server_stderr': server_stderr,
            'server_returncode': server.returncode,
        })
    except subprocess.TimeoutExpired:
        if server and server.poll() is None:
            server.kill()
            server.communicate()
        return jsonify({'ok': False, 'error': 'Cliente/servidor não concluíram dentro do tempo limite.'}), 408
    except Exception as e:
        if server and server.poll() is None:
            server.kill()
            server.communicate()
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.get('/api/download/<ident>')
def download(ident):
    path = _web_executable(ident)
    if not path or not os.path.isfile(path):
        return jsonify({'ok': False, 'error': 'Executável não encontrado'}), 404
    return send_file(path, as_attachment=True, download_name='minipar_program' + ('.exe' if os.name == 'nt' else ''))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
