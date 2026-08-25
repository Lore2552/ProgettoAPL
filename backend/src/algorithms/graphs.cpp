#include "algorithms/graphs.hpp"
#include <cmath>
#include <limits>
#include <algorithm>

const int INF = 99999999;

void dijkstra(const std::vector<int>& adj_matrix, int start_node, MemoryTracer& mem, StepCallback cb) {
    if (adj_matrix.empty()) return;
    int n = static_cast<int>(std::sqrt(adj_matrix.size()));
    if (n * n != (int)adj_matrix.size()) return; // Non è quadrata
    
    if (start_node < 0 || start_node >= n) start_node = 0;

    std::vector<int> dist(n, INF);
    std::vector<bool> visited(n, false);
    dist[start_node] = 0;

    int steps = 0, comps = 0, swaps = 0;

    mem.pushFrame("dijkstra");
    
    // Step iniziale
    if (cb) {
        StepEvent ev;
        ev.step = ++steps;
        ev.array = dist;
        ev.highlight = {start_node};
        ev.comparisons = comps;
        ev.swaps = swaps;
        ev.memory = mem.snapshot();
        cb(ev);
    }

    for (int count = 0; count < n - 1; ++count) {
        // Trova nodo con distanza minima
        int u = -1;
        int min_d = INF;
        for (int v = 0; v < n; ++v) {
            comps++;
            if (!visited[v] && dist[v] <= min_d) {
                min_d = dist[v];
                u = v;
            }
        }

        if (u == -1 || min_d == INF) break; // Resto inarrivabile

        visited[u] = true;

        if (cb) {
            StepEvent ev;
            ev.step = ++steps;
            ev.array = dist;
            ev.highlight = {u}; // Nodo in elaborazione
            ev.comparisons = comps;
            ev.swaps = swaps;
            
            // Aggiorna stack frame con le variabili chiave
            mem.popFrame();
            mem.pushFrame("dijkstra");
            // Aggiungiamo hack: la MemoryTracer non permette di aggiornare facilmente,
            // quindi facciamo un pop e push. Omettiamo per semplicità le variabili locali nel frame.
            
            ev.memory = mem.snapshot();
            cb(ev);
        }

        for (int v = 0; v < n; ++v) {
            int edge_cost = adj_matrix[u * n + v];
            if (edge_cost > 0 && edge_cost != INF && !visited[v] && dist[u] != INF) {
                comps++;
                if (dist[u] + edge_cost < dist[v]) {
                    dist[v] = dist[u] + edge_cost;
                    
                    if (cb) {
                        StepEvent ev;
                        ev.step = ++steps;
                        ev.array = dist;
                        ev.highlight = {u, v}; // Evidenzia l'arco in esame
                        ev.comparisons = comps;
                        ev.swaps = swaps;
                        ev.memory = mem.snapshot();
                        cb(ev);
                    }
                }
            }
        }
    }
    
    // Step finale
    if (cb) {
        StepEvent ev;
        ev.step = ++steps;
        ev.array = dist;
        ev.highlight = {}; 
        ev.comparisons = comps;
        ev.swaps = swaps;
        ev.memory = mem.snapshot();
        cb(ev);
    }

    mem.popFrame();
}

void dijkstraBench(const int* adj_matrix, int n, int start_node) {
    if (start_node < 0 || start_node >= n) start_node = 0;
    std::vector<int> dist(n, INF);
    std::vector<bool> visited(n, false);
    dist[start_node] = 0;

    for (int count = 0; count < n - 1; ++count) {
        int u = -1;
        int min_d = INF;
        for (int v = 0; v < n; ++v) {
            if (!visited[v] && dist[v] <= min_d) {
                min_d = dist[v];
                u = v;
            }
        }

        if (u == -1 || min_d == INF) break;
        visited[u] = true;

        for (int v = 0; v < n; ++v) {
            int edge_cost = adj_matrix[u * n + v];
            if (edge_cost > 0 && edge_cost != INF && !visited[v] && dist[u] != INF) {
                if (dist[u] + edge_cost < dist[v]) {
                    dist[v] = dist[u] + edge_cost;
                }
            }
        }
    }
}
