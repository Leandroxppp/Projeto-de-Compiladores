from flask import Flask, render_template, request, jsonify, send_file
import os
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
    # Somente arquivos .minipar diretamente dentro da pasta tests/ podem ser carregados.
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
    code = request.json.get('code', '')
    try:
        r = compile_source(code, build=False)
        return jsonify({'ok': True, **r})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.post('/api/compile')
def compile_api():
    code = request.json.get('code', '')
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
    ident = request.json.get('id', '')
    path = os.path.join(OUT, 'web_' + ident + ('.exe' if os.name == 'nt' else ''))
    if not os.path.exists(path):
        return jsonify({'ok': False, 'error': 'Executável não encontrado'}), 404
    try:
        return jsonify({'ok': True, **execute(path)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@app.get('/api/download/<ident>')
def download(ident):
    path = os.path.join(OUT, 'web_' + ident + ('.exe' if os.name == 'nt' else ''))
    return send_file(path, as_attachment=True, download_name='minipar_program' + ('.exe' if os.name == 'nt' else ''))


if __name__ == '__main__':
    app.run(debug=True, port=5000)
