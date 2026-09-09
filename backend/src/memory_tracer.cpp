#include "memory_tracer.hpp"
#include <algorithm>

void MemoryTracer::pushFrame(const std::string &funcName,
                             const std::map<std::string, std::string> &vars) {
  MemFrame frame;
  frame.func_name = funcName;
  frame.vars = vars;
  stack_.push_back(frame);
}

void MemoryTracer::popFrame() {
  if (!stack_.empty()) {
    stack_.pop_back();
  }
}

void MemoryTracer::updateFrame(const std::map<std::string, std::string> &vars) {
  if (!stack_.empty()) {
    // Aggiorna (merge) le variabili del frame corrente (top)
    for (const auto &[key, val] : vars) {
      stack_.back().vars[key] = val;
    }
  }
}

void MemoryTracer::heapAlloc(const std::string &label, int size,
                             const std::string &content) {
  // Rimuovi eventuale blocco precedente con stesso label, riallochiamo
  heap_.erase(
      std::remove_if(heap_.begin(), heap_.end(),
                     [&label](const HeapBlock &b) { return b.label == label; }),
      heap_.end());
  heap_.push_back({label, size, content});
}

void MemoryTracer::heapFree(const std::string &label) {
  heap_.erase(
      std::remove_if(heap_.begin(), heap_.end(),
                     [&label](const HeapBlock &b) { return b.label == label; }),
      heap_.end());
}

MemorySnapshot MemoryTracer::snapshot() const { return {stack_, heap_}; }

void MemoryTracer::reset() {
  stack_.clear();
  heap_.clear();
}
