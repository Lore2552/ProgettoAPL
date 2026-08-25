#pragma once
#include <string>
#include <vector>
#include <functional>
#include "memory_tracer.hpp"

// -----------------------------------------------------------------------
// StepEvent — un singolo "passo" dell'algoritmo da inviare al frontend
// -----------------------------------------------------------------------

struct StepEvent {
    int              step;
    std::vector<int> array;       // stato attuale dell'array
    std::vector<int> highlight;   // indici degli elementi "attivi" in questo step
    int              comparisons; // comparazioni totali fino a questo step
    int              swaps;       // swap totali fino a questo step
    MemorySnapshot   memory;      // snapshot Stack/Heap in questo step
};

// Tipo della callback invocata ad ogni step
using StepCallback = std::function<void(const StepEvent&)>;

// -----------------------------------------------------------------------
// Dichiarazioni degli algoritmi di ordinamento
// Ogni funzione modifica arr in-place e invoca cb ad ogni step significativo
// -----------------------------------------------------------------------

void bubbleSort(std::vector<int>& arr, MemoryTracer& mem, StepCallback cb);
void insertionSort(std::vector<int>& arr, MemoryTracer& mem, StepCallback cb);
void selectionSort(std::vector<int>& arr, MemoryTracer& mem, StepCallback cb);
void mergeSort(std::vector<int>& arr, MemoryTracer& mem, StepCallback cb);
void quickSort(std::vector<int>& arr, MemoryTracer& mem, StepCallback cb);

// Versioni Pure (no overhead) per i Benchmark
void bubbleSortBench(int* arr, int n);
void insertionSortBench(int* arr, int n);
void selectionSortBench(int* arr, int n);
void mergeSortBench(int* arr, int n);
void quickSortBench(int* arr, int n);
