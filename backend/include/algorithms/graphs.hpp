#pragma once
#include <vector>
#include <functional>
#include "memory_tracer.hpp"
#include "algorithms/sorting.hpp" // per StepCallback e StepEvent

// -----------------------------------------------------------------------
// Algoritmi sui Grafi
// L'input "adj_matrix" è una matrice di adiacenza N x N "appiattita".
// 0 o -1 indicano assenza di arco.
// L'array emesso ad ogni step rappresenta le "distanze" correnti dal nodo sorgente.
// -----------------------------------------------------------------------

void dijkstra(const std::vector<int>& adj_matrix, int start_node, MemoryTracer& mem, StepCallback cb);

// Versione pura per benchmark
void dijkstraBench(const int* adj_matrix, int n, int start_node);
