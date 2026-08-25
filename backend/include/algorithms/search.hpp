#pragma once
#include <vector>
#include <functional>
#include "memory_tracer.hpp"
#include "sorting.hpp"  // riutilizza StepEvent e StepCallback

// -----------------------------------------------------------------------
// Algoritmi di ricerca
// -----------------------------------------------------------------------

/// Ricerca lineare: cerca target in arr, invoca cb ad ogni confronto
/// Ritorna l'indice trovato, oppure -1 se non presente
int linearSearch(const std::vector<int>& arr, int target,
                 MemoryTracer& mem, StepCallback cb);

// Versioni Pure
int linearSearchBench(const int* arr, int n, int target);
int binarySearchBench(const int* arr, int n, int target);

/// Ricerca binaria: arr deve essere ordinato
/// Ritorna l'indice trovato, oppure -1 se non presente
int binarySearch(const std::vector<int>& arr, int target,
                 MemoryTracer& mem, StepCallback cb);
