import argparse, os, sys
from src.compiler import compile_source, execute
from src.lexer import LexerError
from src.parser import ParseError


def main():
    ap = argparse.ArgumentParser(description='Compilador MiniPar 2026.2')
    ap.add_argument('file', nargs='?')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--no-build', action='store_true')
    a = ap.parse_args()

    if not a.file:
        print(
            'MiniPar 2026.2\n'
            '1) Terminal: python main.py tests/teste8_avaliacao_4_nucleos.minipar --run\n'
            '2) Web desenvolvedor: python app.py -> /dev\n'
            '3) Web didática: python app.py -> /learn'
        )
        return 0

    try:
        src = open(a.file, encoding='utf-8').read()
    except OSError as e:
        print(f'[Arquivo] ERRO: não foi possível abrir {a.file!r}: {e}')
        return 1

    base = os.path.join('output', os.path.splitext(os.path.basename(a.file))[0])

    try:
        r = compile_source(src, base, not a.no_build)
    except LexerError as e:
        print(f'[Lexer] ERRO: {e}')
        return 1
    except ParseError as e:
        print(f'[Parser] ERRO: {e}')
        return 1
    except Exception as e:
        print(f'[Compilador] ERRO interno: {e}')
        return 1

    print('[Lexer] tokens:', len(r['tokens']))
    print('[Parser] AST: OK')

    if r['semantic_errors']:
        print('[Semântico] FALHOU')
        for erro in r['semantic_errors']:
            print(' -', erro)
        print('[Compilação] interrompida por erros semânticos.')
        return 1

    print('[Semântico] OK')
    os.makedirs('output', exist_ok=True)
    open(base + '.tac', 'w', encoding='utf-8').write(r['tac'])
    print('[TAC] output:', base + '.tac')
    print('[C++] output:', base + '.cpp')

    if r.get('build'):
        if r['build']['ok']:
            print('[Build] OK')
        else:
            print('[Build] FALHOU')
            if r['build'].get('stderr'):
                print(r['build']['stderr'])
            return 1

    if a.run and r.get('build', {}).get('ok'):
        try:
            x = execute(r['build']['exe'])
        except Exception as e:
            print(f'[Execução] ERRO: {e}')
            return 1
        print('--- execução ---')
        print(x['stdout'], end='' if x['stdout'].endswith('\n') or not x['stdout'] else '\n')
        if x['stderr']:
            print(x['stderr'], file=sys.stderr, end='' if x['stderr'].endswith('\n') else '\n')
        if x.get('returncode', 0) != 0:
            print(f'[Execução] processo terminou com código {x["returncode"]}')
            return x['returncode'] or 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
