#pragma once
#include "algorithms/sorting.hpp" // per StepCallback e StepEvent
#include "memory_tracer.hpp"
#include <functional>
#include <vector>

// -----------------------------------------------------------------------
// Algoritmi sui Grafi
// L'input "adj_matrix" è una matrice di adiacenza N x N.
// 0 o -1 indicano assenza di arco.
// L'array emesso ad ogni step rappresenta le "distanze" correnti dal nodo
// sorgente.
// -----------------------------------------------------------------------

void dijkstra(const std::vector<int> &adj_matrix, int start_node,
              MemoryTracer &mem, StepCallback cb);

void dijkstraBench(const int *adj_matrix, int n, int start_node);
