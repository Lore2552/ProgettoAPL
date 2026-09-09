#pragma once
#include <map>
#include <string>
#include <vector>

// -----------------------------------------------------------------------
// Strutture dati per i snapshot di memoria Stack/Heap
// -----------------------------------------------------------------------

/// Un frame sullo stack (una chiamata di funzione con le sue variabili locali)
struct MemFrame {
  std::string func_name;
  std::map<std::string, std::string> vars; // nome -> valore (come stringa)
};

/// Un blocco allocato sull'heap
struct HeapBlock {
  std::string label;   // es. "merge_buffer"
  int size;            // numero di elementi
  std::string content; // contenuto dell'array (es. "[1, 2, 3]")
};

/// Snapshot completo della memoria in un dato istante
struct MemorySnapshot {
  std::vector<MemFrame> stack;
  std::vector<HeapBlock> heap;
};

// -----------------------------------------------------------------------
// MemoryTracer — RAII tracker di Stack e Heap
// -----------------------------------------------------------------------

class MemoryTracer {
public:
  MemoryTracer() = default;
  ~MemoryTracer() = default;

  MemoryTracer(const MemoryTracer &) = delete;
  MemoryTracer &operator=(const MemoryTracer &) = delete;

  /// Aggiunge un frame allo stack simulato (es. per chiamate ricorsive)
  void pushFrame(const std::string &funcName,
                 const std::map<std::string, std::string> &vars = {});

  /// Rimuove il frame più recente dallo stack simulato
  void popFrame();

  /// Aggiorna le variabili del frame corrente (top dello stack)
  void updateFrame(const std::map<std::string, std::string> &vars);

  /// Registra un'allocazione heap
  void heapAlloc(const std::string &label, int size,
                 const std::string &content = "");

  /// Rimuove un'allocazione heap
  void heapFree(const std::string &label);

  /// Ritorna uno snapshot dello stato corrente
  MemorySnapshot snapshot() const;

  /// Reset per ogni run
  void reset();

private:
  std::vector<MemFrame> stack_;
  std::vector<HeapBlock> heap_;
};
