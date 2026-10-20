# ==============================================================================
# PASSO 1: RECURSOS NATIVOS (SEM DECLARAÇÃO DE 'IMPORT')
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


# --- 1.3 Captura de Tempo e Módulo Multiprocessing Nativos ---
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
# PASSO 3: FUNÇÕES DOS TRABALHADORES (NÚCLEOS DE CPU)
# ==============================================================================

# --- Tarefa das Correções (Núcleos 1 a 4) ---
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


# --- Tarefa do Fractal de Mandelbrot (Núcleo 5) ---
def trabalhador_fractal(fila_resultados: object):
    """Executado no Núcleo 5: calcula um Fractal de Mandelbrot em arte ASCII."""
    largura = 50
    altura = 20
    max_iter = 100
    caracteres = " .:-=+#%@"

    linhas_fractal = []
    linhas_fractal.append("\n=== FRACTAL DE MANDELBROT (Gerado pelo Núcleo 5) ===")

    for y in range(altura):
        linha = ""
        # Mapeia a coordenada Y para o plano complexo [-1.2, 1.2]
        cy = (y / altura) * 2.4 - 1.2
        for x in range(largura):
            # Mapeia a coordenada X para o plano complexo [-2.0, 1.0]
            cx = (x / largura) * 3.0 - 2.0

            # Equação complexa do Fractal: z = z^2 + c
            zx, zy = 0.0, 0.0
            iteracao = 0
            while zx * zx + zy * zy <= 4.0 and iteracao < max_iter:
                tmp = zx * zx - zy * zy + cx
                zy = 2.0 * zx * zy + cy
                zx = tmp
                iteracao += 1

            # Mapeia o número de iterações para um caractere de texto
            char_idx = int((iteracao / max_iter) * (len(caracteres) - 1))
            linha += caracteres[char_idx]

        linhas_fractal.append(linha)

    linhas_fractal.append("====================================================\n")
    resultado_texto = "\n".join(linhas_fractal)
    fila_resultados.put(("FRACTAL", resultado_texto))


# ==============================================================================
# PASSO 4: EXECUÇÃO SEQUENCIAL E PARALELA
# ==============================================================================


def execucao_sequencial():
    """Modo Sequencial: 1 único núcleo processa as 160 avaliações e gera o fractal."""
    print("--- 1. Executando Modo Sequencial (Apenas 1 Núcleo) ---")
    inicio = obter_tempo()

    # 1. Corrige todas as atividades
    resultados_avaliacoes = []
    for tarefa in tarefas:
        res = avaliar_atividade(tarefa, avaliador="Professor")
        resultados_avaliacoes.append(res)

    # 2. Calcula o fractal no mesmo núcleo
    fila_temp = multiprocessing.Queue()
    trabalhador_fractal(fila_temp)
    _, texto_fractal = fila_temp.get()

    fim = obter_tempo()
    return fim - inicio, texto_fractal


def execucao_paralela():
    """Modo Paralelo: Aloca 5 Núcleos de CPU independentes.

    - Núcleos 1 a 4: Avaliação das Atividades
    - Núcleo 5: Cálculo do Fractal de Mandelbrot
    """
    print("--- 2. Executando Modo Paralelo (5 Núcleos Dedicados) ---")

    num_avaliadores = len(AVALIADORES)
    tamanho_fatia = len(tarefas) // num_avaliadores
    fatias_tarefas = [
        tarefas[i * tamanho_fatia : (i + 1) * tamanho_fatia]
        for i in range(num_avaliadores)
    ]

    fila_resultados = multiprocessing.Queue()
    processos = []

    inicio = obter_tempo()

    # --------------------------------------------------------------------------
    # FOR DE ALOCAÇÃO (FORK): Dispara os 5 processos em núcleos separados
    # --------------------------------------------------------------------------
    # Dispara os 4 núcleos de avaliação
    for i in range(num_avaliadores):
        p = multiprocessing.Process(
            target=trabalhador_avaliacao,
            args=(AVALIADORES[i], fatias_tarefas[i], fila_resultados),
        )
        processos.append(p)

    # Dispara o 5º núcleo (Fractal)
    p_fractal = multiprocessing.Process(
        target=trabalhador_fractal, args=(fila_resultados,)
    )
    processos.append(p_fractal)

    # Inicia a execução em todos os 5 núcleos simultaneamente
    for p in processos:
        p.start()

    # --------------------------------------------------------------------------
    # FOR DE SINCRONIZAÇÃO (JOIN): Coleta resultados e aguarda a conclusão
    # --------------------------------------------------------------------------
    texto_fractal = ""
    for _ in range(len(processos)):
        tipo, dados = fila_resultados.get()
        if tipo == "FRACTAL":
            texto_fractal = dados

    # Garante que os 5 núcleos finalizaram totalmente
    for p in processos:
        p.join()

    fim = obter_tempo()
    return fim - inicio, texto_fractal


# ==============================================================================
# PASSO 5: BENCHMARK E EXIBIÇÃO
# ==============================================================================

if __name__ == "__main__":
    print(
        f"Carga de Trabalho: {TOTAL_ATIVIDADES} atividades + 1 Cálculo de Fractal ASCII\n"
    )

    # 1. Execução Sequencial
    tempo_seq, fractal_seq = execucao_sequencial()
    print(f"Tempo Sequencial Concluído em: {tempo_seq:.2f} segundos\n")

    # 2. Execução Paralela (5 Núcleos)
    tempo_par, fractal_par = execucao_paralela()
    print(f"Tempo Paralelo Concluído em:   {tempo_par:.2f} segundos\n")

    # Exibe a saída do fractal gerado no processamento paralelo
    print(fractal_par)

    # 3. Métricas do Benchmark
    speedup = tempo_seq / tempo_par
    reducao_pct = ((tempo_seq - tempo_par) / tempo_seq) * 100

    print("==========================================")
    print("         BENCHMARK DE DESEMPENHO          ")
    print("==========================================")
    print(f"Núcleos Utilizados (Paralelo) : 5")
    print(f"Tempo Sequencial             : {tempo_seq:.2f} s")
    print(f"Tempo Paralelo               : {tempo_par:.2f} s")
    print(f"Aceleração (Speedup)         : {speedup:.2f}x mais rápido!")
    print(f"Redução de Tempo             : {reducao_pct:.1f}%")
    print("==========================================")
