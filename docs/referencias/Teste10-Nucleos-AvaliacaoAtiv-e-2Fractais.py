# ==============================================================================
# PASSO 1: RECURSOS NATIVOS (SEM DECLARAÇÃO DE 'IMPORT' NO TOPO)
# ==============================================================================

# --- 1.1 Gerador de Números Pseudoaleatórios (LCG) ---
_estado_random = 123456789


def meu_random_uniforme(minimo: float, maximo: float) -> float:
    """Gera um decimal aleatório entre 'minimo' e 'maximo'."""
    global _estado_random
    _estado_random = (_estado_random * 1103515245 + 12345) & 0x7FFFFFFF
    fracao = _estado_random / 2147483647.0
    return minimo + (maximo - minimo) * fracao


# --- 1.2 Simulação de Carga de CPU ---
def simular_atraso(segundos: float):
    """Consome ciclos de CPU para simular o tempo de trabalho."""
    iteracoes = int(segundos * 1_500_000)
    soma = 0
    for i in range(iteracoes):
        soma += i


# --- 1.3 Captura de Tempo e Multiprocessing Nativos ---
def obter_tempo() -> float:
    """Acessa o relógio de alta precisão do SO via __import__."""
    return __import__("time").perf_counter()


multiprocessing = __import__("multiprocessing")


# ==============================================================================
# PASSO 2: CONFIGURAÇÃO DO CENÁRIO
# ==============================================================================

NUM_ALUNOS = 40
ATIVIDADES_POR_ALUNO = 4
TOTAL_ATIVIDADES = NUM_ALUNOS * ATIVIDADES_POR_ALUNO  # 160 atividades

AVALIADORES = ["Professor", "Monitor 1", "Monitor 2", "Monitor 3"]

# Criamos as 160 tarefas de avaliação
tarefas = [
    f"Aluno {aluno_id + 1} - Atividade {atividade_id + 1}"
    for aluno_id in range(NUM_ALUNOS)
    for atividade_id in range(ATIVIDADES_POR_ALUNO)
]


# ==============================================================================
# PASSO 3: FUNÇÕES DOS TRABALHADORES (NÚCLEOS DE CPU 1 A 6)
# ==============================================================================

# --- Núcleos 1 a 4: Correção das Atividades ---
def avaliar_atividade(tarefa: str, avaliador: str) -> str:
    tempo_correcao = meu_random_uniforme(0.05, 0.15)
    simular_atraso(tempo_correcao)
    return f"[{avaliador}] Concluiu: {tarefa}"


def trabalhador_avaliacao(
    avaliador: str, lote_tarefas: list, fila_resultados: object
):
    """Executado nos Núcleos 1 a 4: processa o lote de correções."""
    resultados_locais = []
    for tarefa in lote_tarefas:
        res = avaliar_atividade(tarefa, avaliador)
        resultados_locais.append(res)
    fila_resultados.put(("AVALIACAO", resultados_locais))


# --- Núcleo 5: Fractal de Mandelbrot (ASCII) ---
def trabalhador_mandelbrot(fila_resultados: object):
    """Executado no Núcleo 5: calcula o Fractal de Mandelbrot em texto ASCII."""
    largura, altura, max_iter = 50, 20, 100
    caracteres = " .:-=+#%@"

    linhas_fractal = [
        "\n=== FRACTAL DE MANDELBROT (Gerado pelo Núcleo 5) ==="
    ]
    for y in range(altura):
        linha = ""
        cy = (y / altura) * 2.4 - 1.2
        for x in range(largura):
            cx = (x / largura) * 3.0 - 2.0
            zx, zy, iteracao = 0.0, 0.0, 0
            while zx * zx + zy * zy <= 4.0 and iteracao < max_iter:
                tmp = zx * zx - zy * zy + cx
                zy = 2.0 * zx * zy + cy
                zx = tmp
                iteracao += 1
            linha += caracteres[
                int((iteracao / max_iter) * (len(caracteres) - 1))
            ]
        linhas_fractal.append(linha)
    linhas_fractal.append("====================================================\n")
    fila_resultados.put(("MANDELBROT", "\n".join(linhas_fractal)))


# --- Núcleo 6: Fractal do Tapete de Sierpinski (Desenho Correto com Turtle) ---
def desenhar_quadrado(x, y, tamanho, cor, t_obj):
    """Desenha um quadrado preenchido centrado em (x, y)."""
    t_obj.up()
    t_obj.goto(x - tamanho / 2, y - tamanho / 2)
    t_obj.down()
    t_obj.color(cor)
    t_obj.begin_fill()
    for _ in range(4):
        t_obj.forward(tamanho)
        t_obj.left(90)
    t_obj.end_fill()


def desenhar_tapete_sierpinski(x, y, lado, grau, t_obj):
    """Algoritmo recursivo que remove/desenha os centros brancos do tapete."""
    if grau <= 0:
        return

    # Desenha o quadrado central "vazio" (branco)
    tamanho_centro = lado / 3
    desenhar_quadrado(x, y, tamanho_centro, "white", t_obj)

    novo_lado = lado / 3
    novo_grau = grau - 1

    # Chamadas recursivas para os 8 sub-quadrados periféricos
    desenhar_tapete_sierpinski(
        x - novo_lado, y + novo_lado, novo_lado, novo_grau, t_obj
    )
    desenhar_tapete_sierpinski(x, y + novo_lado, novo_lado, novo_grau, t_obj)
    desenhar_tapete_sierpinski(
        x + novo_lado, y + novo_lado, novo_lado, novo_grau, t_obj
    )

    desenhar_tapete_sierpinski(x - novo_lado, y, novo_lado, novo_grau, t_obj)
    desenhar_tapete_sierpinski(x + novo_lado, y, novo_lado, novo_grau, t_obj)

    desenhar_tapete_sierpinski(
        x - novo_lado, y - novo_lado, novo_lado, novo_grau, t_obj
    )
    desenhar_tapete_sierpinski(x, y - novo_lado, novo_lado, novo_grau, t_obj)
    desenhar_tapete_sierpinski(
        x + novo_lado, y - novo_lado, novo_lado, novo_grau, t_obj
    )


def executar_trabalhador_sierpinski():
    """Inicializa o canvas do Turtle e desenha o Tapete de Sierpinski."""
    turtle = __import__("turtle")

    # Configuração de tela e velocidade
    screen = turtle.Screen()
    screen.title("Núcleo 6 - Tapete de Sierpinski")
    screen.bgcolor("black")

    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()
    screen.tracer(0, 0)  # Desativa animação para desenhar instantaneamente

    # 1. Desenha o bloco principal inicial (azul)
    lado_inicial = 300
    desenhar_quadrado(0, 0, lado_inicial, "navy", t)

    # 2. Executa a perfuração recursiva (grau 4)
    desenhar_tapete_sierpinski(0, 0, lado_inicial, 4, t)

    screen.update()
    print(
        "-> [Núcleo 6] Tapete de Sierpinski renderizado com sucesso na tela!"
    )


# ==============================================================================
# PASSO 4: EXECUÇÃO SEQUENCIAL E PARALELA
# ==============================================================================


def execucao_sequencial():
    """Modo Sequencial: 1 único núcleo processa as 160 avaliações e os 2 fractais."""
    print("--- 1. Executando Modo Sequencial (Apenas 1 Núcleo) ---")
    inicio = obter_tempo()

    # 1. Atividades
    resultados_avaliacoes = []
    for tarefa in tarefas:
        res = avaliar_atividade(tarefa, avaliador="Professor")
        resultados_avaliacoes.append(res)

    # 2. Mandelbrot
    fila_temp = multiprocessing.Queue()
    trabalhador_mandelbrot(fila_temp)
    _, texto_mandelbrot = fila_temp.get()

    fim = obter_tempo()
    return fim - inicio, texto_mandelbrot


def execucao_paralela():
    """Modo Paralelo: Aloca 6 Núcleos de CPU independentes."""
    print("--- 2. Executando Modo Paralelo (6 Núcleos Dedicados) ---")

    num_avaliadores = len(AVALIADORES)
    tamanho_fatia = len(tarefas) // num_avaliadores
    fatias_tarefas = [
        tarefas[i * tamanho_fatia : (i + 1) * tamanho_fatia]
        for i in range(num_avaliadores)
    ]

    fila_resultados = multiprocessing.Queue()
    processos = []

    inicio = obter_tempo()

    # Dispara os 4 núcleos de avaliação
    for i in range(num_avaliadores):
        p = multiprocessing.Process(
            target=trabalhador_avaliacao,
            args=(AVALIADORES[i], fatias_tarefas[i], fila_resultados),
        )
        processos.append(p)

    # Dispara o 5º núcleo (Mandelbrot)
    p_mandelbrot = multiprocessing.Process(
        target=trabalhador_mandelbrot, args=(fila_resultados,)
    )
    processos.append(p_mandelbrot)

    # Inicia os 5 primeiros núcleos assíncronos
    for p in processos:
        p.start()

    # Coleta de resultados
    texto_mandelbrot = ""
    for _ in range(len(processos)):
        tipo, dados = fila_resultados.get()
        if tipo == "MANDELBROT":
            texto_mandelbrot = dados

    for p in processos:
        p.join()

    # Executa a renderização gráfica no 6º núcleo
    executar_trabalhador_sierpinski()

    fim = obter_tempo()
    return fim - inicio, texto_mandelbrot


# ==============================================================================
# PASSO 5: BENCHMARK E EXIBIÇÃO
# ==============================================================================

if __name__ == "__main__":
    print(
        f"Carga de Trabalho: {TOTAL_ATIVIDADES} atividades + Mandelbrot (ASCII) + Sierpinski (Turtle)\n"
    )

    # 1. Execução Sequencial
    tempo_seq, mandelbrot_seq = execucao_sequencial()
    print(f"Tempo Sequencial Concluído em: {tempo_seq:.2f} segundos\n")

    # 2. Execução Paralela (6 Núcleos)
    tempo_par, mandelbrot_par = execucao_paralela()
    print(f"Tempo Paralelo Concluído em:   {tempo_par:.2f} segundos\n")

    # Exibe o fractal de Mandelbrot gerado em texto
    print(mandelbrot_par)

    # 3. Métricas do Benchmark
    speedup = tempo_seq / tempo_par
    reducao_pct = ((tempo_seq - tempo_par) / tempo_seq) * 100

    print("==========================================")
    print("         BENCHMARK DE DESEMPENHO          ")
    print("==========================================")
    print(f"Núcleos Utilizados (Paralelo) : 6")
    print(f"Tempo Sequencial             : {tempo_seq:.2f} s")
    print(f"Tempo Paralelo               : {tempo_par:.2f} s")
    print(f"Aceleração (Speedup)         : {speedup:.2f}x mais rápido!")
    print(f"Redução de Tempo             : {reducao_pct:.1f}%")
    print("==========================================")

    # Mantém a janela gráfica aberta até o clique do usuário
    try:
        __import__("turtle").done()
    except Exception:
        pass
