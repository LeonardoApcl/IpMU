import numpy as np
import random
from collections import defaultdict

def obter_arestas_do_caminho(origem, destino, matriz_predecessores):
    """Reconstrói o caminho e retorna a lista de arestas (u, v) usadas."""
    if matriz_predecessores[origem][destino] == -1:
        return []
    
    arestas = []
    atual = origem
    while atual != destino:
        prox = matriz_predecessores[atual][destino]
        arestas.append((atual, prox))
        atual = prox
    return arestas

def avaliar_candidato_com_orcamento(S_temporario, num_clientes, matriz_tempo, matriz_custo_original, pred_tempo, orcamento_B):
    """Realiza o Fast Upgrading Procedure do artigo para avaliar uma possível solução."""
    frequencia_arestas = defaultdict(int)
    custo_total_original = 0
    
    for i in range(num_clientes):
        # A mediana é quem envia para o cliente. 
        # Procura o menor tempo de alguma mediana da solução para o cliente 'i'
        melhor_mediana = min(S_temporario, key=lambda m: matriz_tempo[m][i])
        
        # Se o cliente não puder ser atendido (grafo desconexo), o custo dessa solução é infinito
        if matriz_tempo[melhor_mediana][i] == float('inf'):
            custo_total_original += float('inf')
            continue
            
        arestas_caminho = obter_arestas_do_caminho(melhor_mediana, i, pred_tempo)
        for u, v in arestas_caminho:
            frequencia_arestas[(u, v)] += 1
            custo_total_original += matriz_custo_original[u][v]
            
    # Ordena as arestas mais usadas para receberem o orçamento primeiro
    arestas_ordenadas = sorted(frequencia_arestas.items(), key=lambda item: item[1], reverse=True)
    economia_total = 0
    orcamento_restante = orcamento_B
    arestas_melhoradas = {}
    
    for (u, v), freq in arestas_ordenadas:
        if orcamento_restante <= 0:
            break
        # Relaxamento máximo igual ao custo original (ua = ca^2)
        capacidade_maxima_aresta = matriz_custo_original[u][v]
        investimento = min(orcamento_restante, capacidade_maxima_aresta)
        economia_total += investimento * freq
        orcamento_restante -= investimento
        arestas_melhoradas[(u, v)] = matriz_custo_original[u][v] - investimento
        
    return custo_total_original - economia_total, frequencia_arestas, arestas_melhoradas

def construcao_grasp_ipmu(matriz_tempo, matriz_custo_original, pred_tempo, num_clientes, p, alpha, orcamento_B):
    """Constrói a solução iterativamente."""
    S = []
    candidatos_disponiveis = list(range(num_clientes))
    melhor_frequencia = {}
    melhor_arestas_melhoradas = {}
    
    while len(S) < p:
        custos_candidatos = {}
        dados_candidatos = {}
        
        # Avalia a viabilidade de adicionar cada candidato
        for c in candidatos_disponiveis:
            S_temporario = S + [c]
            custo_c, freq, melhoradas = avaliar_candidato_com_orcamento(
                S_temporario, num_clientes, matriz_tempo, matriz_custo_original, pred_tempo, orcamento_B
            )
            custos_candidatos[c] = custo_c
            dados_candidatos[c] = (freq, melhoradas)
            
        c_min = min(custos_candidatos.values())
        
        if c_min == float('inf'):
            # Nenhum candidato resolve o problema de acesso ainda, pegamos todo mundo para RCL
            RCL = candidatos_disponiveis
        else:
            c_max = max([c for c in custos_candidatos.values() if c != float('inf')])
            limiar = c_min + alpha * (c_max - c_min)
            RCL = [c for c, custo in custos_candidatos.items() if custo <= limiar]
            
        x = random.choice(RCL)
        S.append(x)
        candidatos_disponiveis.remove(x)
        
        # Guardamos a rota da última mediana inserida para facilitar o log no fim
        melhor_frequencia = dados_candidatos[x][0]
        melhor_arestas_melhoradas = dados_candidatos[x][1]
        
    return S, list(melhor_frequencia.keys()), melhor_arestas_melhoradas