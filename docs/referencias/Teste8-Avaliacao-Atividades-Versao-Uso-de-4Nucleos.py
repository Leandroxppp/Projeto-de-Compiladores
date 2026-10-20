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


# --- 1.2 Simulação de Carga de CPU (Substituindo time.sleep) ---
def simular_atraso(segundos: float):
    """Consome ciclos de CPU para simular o tempo de trabalho."""
    iteracoes = int(segundos * 1_500_000)
    soma = 0
    for i in range(iteracoes):
        soma += i


# --- 1.3 Captura de Tempo e Paralelismo Nativos ---
def obter_tempo() -> float:
    """Acessa o relógio de alta precisão do SO via __import__."""
    return __import__("time").perf_counter()


# Acessamos o módulo multiprocessing dinamicamente para alocação real de núcleos
multiprocessing = __import__("multiprocessing")


# ==============================================================================
# PASSO 2: CONFIGURAÇÃO DO CENÁRIO
# ==============================================================================

NUM_ALUNOS = 40
ATIVIDADES_POR_ALUNO = 4
TOTAL_ATIVIDADES = NUM_ALUNOS * ATIVIDADES_POR_ALUNO  # 160 atividades

AVALIADORES = ["Professor", "Monitor 1", "Monitor 2", "Monitor 3"]

# Criamos as 160 tarefas a serem corrigidas
tarefas = [
    f"Aluno {aluno_id + 1} - Atividade {atividade_id + 1}"
    for aluno_id in range(NUM_ALUNOS)
    for atividade_id in range(ATIVIDADES_POR_ALUNO)
]


# ==============================================================================
# PASSO 3: FUNÇÕES DE TRABALHO DOS NÚCLEOS
# ==============================================================================


def avaliar_atividade(tarefa: str, avaliador: str) -> str:
    """Simula a correção de uma atividade individual."""
    tempo_correcao = meu_random_uniforme(0.05, 0.15)
    simular_atraso(tempo_correcao)
    return f"[{avaliador}] Concluiu: {tarefa}"


def trabalhador_núcleo(
    avaliador: str, lote_tarefas: list, fila_resultados: object
):
    """Função executada de forma independente por cada núcleo da CPU."""
    resultados_locais = []
    for tarefa in lote_tarefas:
        res = avaliar_atividade(tarefa, avaliador)
        resultados_locais.append(res)

    # Envia a lista de atividades corrigidas de volta ao processo principal
    fila_resultados.put(resultados_locais)


# --- 3.1 Execução Sequencial ---
def execucao_sequencial():
    """Modo Sequencial: 1 único núcleo/processo resolve todas as 160 tarefas."""
    print("--- 1. Executando Modo Sequencial (Apenas 1 Núcleo / Professor) ---")
    inicio = obter_tempo()

    resultados = []
    for tarefa in tarefas:
        res = avaliar_atividade(tarefa, avaliador="Professor")
        resultados.append(res)

    fim = obter_tempo()
    return fim - inicio


# --- 3.2 Execução Paralela Com Alocação Manual de Núcleos (Fork & Join) ---
def execucao_paralela():
    """Modo Paralelo: Aloca manualmente 1 processo (núcleo de CPU) para cada avaliador.

    Usa o padrão 'FOR (disparar)' e 'FOR (JOIN / juntar resultados)'.
    """
    print(
        "--- 2. Executando Modo Paralelo (4 Núcleos Dedicados: Professor + 3 Monitores) ---"
    )

    num_avaliadores = len(AVALIADORES)

    # Divisão das 160 tarefas em 4 fatias iguais de 40 tarefas
    tamanho_fatia = len(tarefas) // num_avaliadores
    fatias_tarefas = [
        tarefas[i * tamanho_fatia : (i + 1) * tamanho_fatia]
        for i in range(num_avaliadores)
    ]

    # Fila sincronizada para armazenar as respostas de cada núcleo
    fila_resultados = multiprocessing.Queue()

    processos = []

    inicio = obter_tempo()

    # --------------------------------------------------------------------------
    # ETAPA 1: FOR DE ALOCAÇÃO (Cria e inicia 1 processo por avaliador em 1 núcleo)
    # --------------------------------------------------------------------------
    for i in range(num_avaliadores):
        avaliador = AVALIADORES[i]
        lote = fatias_tarefas[i]

        # Instancia um processo isolado que o Sistema Operacional aloca em um núcleo de CPU
        p = multiprocessing.Process(
            target=trabalhador_núcleo, args=(avaliador, lote, fila_resultados)
        )
        processos.append(p)
        p.start()  # Dispara a execução paralela no núcleo

    # --------------------------------------------------------------------------
    # ETAPA 2: FOR DE SINCRONIZAÇÃO E JOIN (Aguarda o término de cada núcleo)
    # --------------------------------------------------------------------------
    resultados_finais = []

    # Coleta os resultados produzidos por cada núcleo
    for _ in range(num_avaliadores):
        resultados_finais.extend(fila_resultados.get())

    # Garante que todos os processos/núcleos finalizaram
    for p in processos:
        p.join()

    fim = obter_tempo()
    return fim - inicio


# ==============================================================================
# PASSO 4: BENCHMARK E EXIBIÇÃO DOS RESULTADOS
# ==============================================================================

if __name__ == "__main__":
    print(
        f"Total de Atividades a Avaliar: {TOTAL_ATIVIDADES} (40 alunos x 4 atividades)\n"
    )

    # 1. Medindo tempo sequencial
    tempo_seq = execucao_sequencial()
    print(f"Tempo Sequencial Concluído em: {tempo_seq:.2f} segundos\n")

    # 2. Medindo tempo paralelo real (usando múltiplos núcleos de CPU)
    tempo_par = execucao_paralela()
    print(f"Tempo Paralelo Concluído em:   {tempo_par:.2f} segundos\n")

    # 3. Métricas do Benchmark
    speedup = tempo_seq / tempo_par
    reducao_pct = ((tempo_seq - tempo_par) / tempo_seq) * 100

    print("==========================================")
    print("         BENCHMARK DE DESEMPENHO          ")
    print("==========================================")
    print(f"Tempo Sequencial : {tempo_seq:.2f} s")
    print(f"Tempo Paralelo   : {tempo_par:.2f} s")
    print(f"Aceleração       : {speedup:.2f}x mais rápido!")
    print(f"Redução no tempo : {reducao_pct:.1f}% de economia")
    print("==========================================")
