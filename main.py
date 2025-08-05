import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
import csv
import os

# --- Parâmetros da Simulação ---
TAMANHO_GRADE = 200
PASSOS = 250 # Aumentado para observar mais a dinâmica
BETA = 0.1 # Probabilidade de infecção para SUSCETÍVEIS ao entrar em contato com um infectado
PROB_INFEC_RESISTENTE = 0.05 # Probabilidade de infecção para RESISTENTES
PROB_RECUPERACAO_DIARIA = 0.15 # Probabilidade diária de um infectado se recuperar
TEMPO_MIN_INFEC = 5 # Tempo mínimo que um indivíduo permanece infectado antes de poder recuperar

NUM_INFECTADOS_INICIAIS = 5 # Número de pontos de infecção iniciais
PERCENTUAL_RESISTENTES = 0.15 # 15% da população inicia como resistente (mas não imune)

# --- Definição dos Estados ---
SUSCETIVEL = 0
INFECTADO = 1
RECUPERADO = 2
RESISTENTE = 3 

# --- Inicialização da Grade ---
grade_estado = np.zeros((TAMANHO_GRADE, TAMANHO_GRADE), dtype=int)
grade_tempo_infectado = np.zeros((TAMANHO_GRADE, TAMANHO_GRADE), dtype=int) # Tempo que o indivíduo está infectado

# Inicializa indivíduos Resistentes aleatoriamente
num_celulas_resistentes = int(TAMANHO_GRADE * TAMANHO_GRADE * PERCENTUAL_RESISTENTES)
celulas_disponiveis = [(r, c) for r in range(TAMANHO_GRADE) for c in range(TAMANHO_GRADE)]
random.shuffle(celulas_disponiveis) # Embaralha as posições para seleção aleatória

for i in range(num_celulas_resistentes):
    # Pega uma posição aleatória sem repetição e define como RESISTENTE
    r, c = celulas_disponiveis.pop()
    grade_estado[r, c] = RESISTENTE

# Inicializa múltiplos pontos de infecção aleatórios
# Garantimos que os pontos iniciais são SUSCETÍVEIS ou RESISTENTES, mas NÃO INFECTADOS
# E se for um resistente, ele vai para INFECTADO, mas sua "resistência" não conta na inicialização
infectados_adicionados = 0
while infectados_adicionados < NUM_INFECTADOS_INICIAIS:
    r, c = random.randint(0, TAMANHO_GRADE - 1), random.randint(0, TAMANHO_GRADE - 1)
    if grade_estado[r, c] != INFECTADO: # Evita infectar a mesma célula duas vezes
        grade_estado[r, c] = INFECTADO
        grade_tempo_infectado[r, c] = 0 # Inicia o tempo de infecção
        infectados_adicionados += 1

# --- Funções Auxiliares ---
def vizinhos(i, j):
    """Retorna as coordenadas dos 8 vizinhos de uma célula (Vizinhança de Moore)."""
    return [(i + x, j + y) for x in [-1, 0, 1] for y in [-1, 0, 1]
            if (x != 0 or y != 0) and 0 <= i + x < TAMANHO_GRADE and 0 <= j + y < TAMANHO_GRADE]

# --- Configuração de Saída (CSV e MP4) ---
os.makedirs("resultados", exist_ok=True)
dados_csv_path = os.path.join("resultados", "dados.csv")
dados_csv = open(dados_csv_path, "w", newline="")
writer = csv.writer(dados_csv)
writer.writerow(["Passo", "Suscetíveis", "Infectados", "Recuperados", "Resistentes"])

# --- Função de Atualização da Simulação (por passo de tempo) ---
def atualizar(frame):
    global grade_estado, grade_tempo_infectado
    nova_grade_estado = np.copy(grade_estado)
    nova_grade_tempo_infectado = np.copy(grade_tempo_infectado)

    suscetiveis = infectados = recuperados = resistentes = 0

    for i in range(TAMANHO_GRADE):
        for j in range(TAMANHO_GRADE):
            estado_atual = grade_estado[i, j]

            if estado_atual == SUSCETIVEL:
                suscetiveis += 1
                for vi, vj in vizinhos(i, j):
                    if grade_estado[vi, vj] == INFECTADO and random.random() < BETA:
                        nova_grade_estado[i, j] = INFECTADO
                        nova_grade_tempo_infectado[i, j] = 0 # Reseta o contador de tempo para o novo infectado
                        break # Já infectou, não precisa verificar outros vizinhos
            
            elif estado_atual == RESISTENTE: 
                resistentes += 1
                for vi, vj in vizinhos(i, j):
                    if grade_estado[vi, vj] == INFECTADO and random.random() < PROB_INFEC_RESISTENTE:
                        nova_grade_estado[i, j] = INFECTADO
                        nova_grade_tempo_infectado[i, j] = 0 # Reseta o contador de tempo para o novo infectado
                        break # Já infectou, não precisa verificar outros vizinhos
            
            elif estado_atual == INFECTADO:
                infectados += 1
                nova_grade_tempo_infectado[i, j] += 1 # Incrementa o tempo de infecção

                # Condição de recuperação com base em probabilidade e tempo mínimo
                if nova_grade_tempo_infectado[i, j] >= TEMPO_MIN_INFEC and random.random() < PROB_RECUPERACAO_DIARIA:
                    nova_grade_estado[i, j] = RECUPERADO
            
            elif estado_atual == RECUPERADO:
                recuperados += 1
                # Recuperados permanecem recuperados neste modelo SIR básico

    # Atualiza as grades com os novos estados e tempos
    grade_estado[:] = nova_grade_estado
    grade_tempo_infectado[:] = nova_grade_tempo_infectado

    # Escreve os dados no CSV
    writer.writerow([frame, suscetiveis, infectados, recuperados, resistentes])

    # Atualiza a visualização
    im.set_array(grade_estado)
    return [im]

# --- Configuração da Visualização ---
fig, ax = plt.subplots(figsize=(8, 8))
# Cores: SUSCETIVEL (verde claro), INFECTADO (vermelho), RECUPERADO (azul), RESISTENTE (cinza mais escuro para diferenciar)
cores = ['#90EE90', '#FF0000', "#0381AB", "#C2DA07"] 
cmap = plt.matplotlib.colors.ListedColormap(cores)
norm = plt.matplotlib.colors.BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N) # Define os limites para 4 estados

im = ax.imshow(grade_estado, cmap=cmap, norm=norm) 

# Adiciona o colorbar com os rótulos corretos
cbar = plt.colorbar(im, ticks=[0, 1, 2, 3], label="Estado")
cbar.set_ticklabels(['Suscetível', 'Infectado', 'Recuperado', 'Resistente (Parcial)'])

plt.title("Simulação SIR com Resistência Parcial")
ax.set_xticks([]) # Remove os ticks do eixo X
ax.set_yticks([]) # Remove os ticks do eixo Y

# --- Criação e Salvamento da Animação ---
ani = animation.FuncAnimation(fig, atualizar, frames=PASSOS, interval=100, blit=True)
ani.save(os.path.join("resultados", "simulacao.mp4"), writer='ffmpeg', dpi=200)
plt.show()

# --- Fecha o arquivo CSV ---
dados_csv.close()
print(f"Simulação concluída. Resultados salvos em '{os.path.abspath('resultados')}'")