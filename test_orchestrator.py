from pathlib import Path
from src.compiler import compile_source

def main():
    ok=0; total=0
    for f in sorted(Path('tests').glob('*.minipar')):
        total+=1
        try:
            r=compile_source(f.read_text(encoding='utf-8'),str(Path('output')/f.stem),True)
            good=not r['semantic_errors'] and r.get('build',{}).get('ok',False)
            print(('[OK] ' if good else '[FALHOU] ')+f.name)
            if not good: print(r.get('semantic_errors'),r.get('build',{}).get('stderr',''))
            ok+=int(good)
        except Exception as e: print('[ERRO]',f.name,e)
    print(f'\nResultado: {ok}/{total} programas compilados com sucesso.')
    raise SystemExit(0 if ok==total else 1)
if __name__=='__main__':main()
