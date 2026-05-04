import networkx as nx
import matplotlib.pyplot as plt
import math

def desenhar_grafo_inicial(matriz_custo, num_clientes):
    """
    Desenha o grafo no seu estado inicial, exibindo todos os custos.
    """
    G = nx.DiGraph() # Grafo direcionado
    
    # Adiciona os nós
    G.add_nodes_from(range(num_clientes))
    
    # Adiciona as arestas baseadas na matriz de custo (ignorando a diagonal principal ou custos infinitos)
    for i in range(num_clientes):
        for j in range(num_clientes):
            if i != j and matriz_custo[i][j] < float('inf'):
                G.add_edge(i, j, weight=matriz_custo[i][j])
                
    plt.figure(figsize=(8, 6))
    plt.title("Estado Inicial do Grafo (Custos)")
    
    # Define o layout (circular costuma ficar bom para problemas de p-median)
    pos = {}
    for i in range(num_clientes):
        # math.pi aponta para a esquerda. Subtrair o ângulo faz girar no sentido horário.
        angulo = math.pi - i * (2 * math.pi / num_clientes)
        pos[i] = (math.cos(angulo), math.sin(angulo))
    
    # Desenha os nós (brancos com borda preta)
    nx.draw_networkx_nodes(G, pos, node_color='white', edgecolors='black', node_size=800)
    nx.draw_networkx_labels(G, pos)
    
    # Desenha as arestas
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20)
    
    # Adiciona os rótulos de peso (custo) nas arestas
    labels_arestas = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_arestas, label_pos=0.3)
    
    plt.axis('off')
    plt.show()

def desenhar_solucao(matriz_custo, num_clientes, medianas_S, arestas_ativas, arestas_melhoradas):
    """
    Desenha o grafo da solução, destacando as medianas e as rotas dos clientes.
    - medianas_S: lista com as medianas escolhidas [ex: 0, 1]
    - arestas_ativas: lista de tuplas com as arestas usadas pelos clientes [(origem, destino), ...]
    - arestas_melhoradas: dicionário com as arestas que receberam orçamento {(u, v): novo_custo}
    """
    G = nx.DiGraph()
    G.add_nodes_from(range(num_clientes))
    
    for i in range(num_clientes):
        for j in range(num_clientes):
            if i != j and matriz_custo[i][j] < float('inf'):
                G.add_edge(i, j, weight=matriz_custo[i][j])
                
    plt.figure(figsize=(8, 6))
    plt.title("Solução IpMU (Medianas e Rotas)")
    pos = {}
    for i in range(num_clientes):
        # math.pi aponta para a esquerda. Subtrair o ângulo faz girar no sentido horário.
        angulo = math.pi - i * (2 * math.pi / num_clientes)
        pos[i] = (math.cos(angulo), math.sin(angulo))
    
    # 1. Desenha os nós separando Clientes (Brancos) de Medianas (Vermelhos)
    nos_clientes = [n for n in G.nodes() if n not in medianas_S]
    nx.draw_networkx_nodes(G, pos, nodelist=nos_clientes, node_color='white', edgecolors='black', node_size=800)
    nx.draw_networkx_nodes(G, pos, nodelist=medianas_S, node_color='red', edgecolors='black', node_size=800)
    nx.draw_networkx_labels(G, pos)
    
    # 2. Divide as arestas em Inativas (Cinza claro) e Ativas (Pretas)
    todas_arestas = list(G.edges())
    arestas_inativas = [e for e in todas_arestas if e not in arestas_ativas]
    
    # Arestas de fundo (não usadas)
    nx.draw_networkx_edges(G, pos, edgelist=arestas_inativas, edge_color='lightgray', arrows=True, style='dashed')
    # Arestas ativas (caminho dos clientes)
    nx.draw_networkx_edges(G, pos, edgelist=arestas_ativas, edge_color='black', arrows=True, width=2)
    
    # 3. Rótulos das arestas
    labels_todas = nx.get_edge_attributes(G, 'weight')
    labels_exibicao = {}
    
    for u, v in arestas_ativas:
        # Se a aresta recebeu orçamento, mostra o novo custo, senão o custo original
        if (u, v) in arestas_melhoradas:
            labels_exibicao[(u, v)] = f"{arestas_melhoradas[(u, v)]}*" # Asterisco para indicar melhoria
        else:
            labels_exibicao[(u, v)] = labels_todas[(u, v)]
            
    # Desenha apenas os rótulos das arestas ativas para não poluir visualmente
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_exibicao, label_pos=0.3, font_color='black', font_weight='bold')
    
    plt.axis('off')
    plt.show()