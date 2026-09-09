#pragma once
#include "nlohmann/json.hpp"
#include "memory_tracer.hpp"
#include "benchmark.hpp"
#include "algorithms/sorting.hpp"

using json = nlohmann::json;

// -----------------------------------------------------------------------
// Conversioni to_json per le struct del progetto (ADL pattern)
// Ogni funzione produce JSON con chiavi identiche al contratto middleware Go
// -----------------------------------------------------------------------

// MemFrame → {"name": "...", "vars": {"k": "v", ...}}
inline void to_json(json& j, const MemFrame& f) {
    j = json{{"name", f.func_name}, {"vars", f.vars}};
}

// HeapBlock → {"label": "...", "size": N, "content": "..."}
inline void to_json(json& j, const HeapBlock& b) {
    j = json{{"label", b.label}, {"size", b.size}, {"content", b.content}};
}

// MemorySnapshot → {"stack": [...], "heap": [...]}
inline void to_json(json& j, const MemorySnapshot& s) {
    j = json{{"stack", s.stack}, {"heap", s.heap}};
}

// StepEvent → {"step": N, "array": [...], "highlight": [...], ...}
inline void to_json(json& j, const StepEvent& e) {
    j = json{
        {"step",        e.step},
        {"array",       e.array},
        {"highlight",   e.highlight},
        {"comparisons", e.comparisons},
        {"swaps",       e.swaps},
        {"memory",      e.memory}
    };
}

// BenchmarkResult → {"algorithm": "...", "n": N, "runs": N, "stats": {...}}
inline void to_json(json& j, const BenchmarkResult& r) {
    j = json{
        {"algorithm", r.algorithm},
        {"n",         r.n},
        {"runs",      r.runs},
        {"stats", {
            {"mean_ns",      r.mean_ns},
            {"median_ns",    r.median_ns},
            {"q1_ns",        r.q1_ns},
            {"q3_ns",        r.q3_ns},
            {"std_dev_ns",   r.std_dev_ns},
            {"run_times_ns", r.run_times_ns}
        }}
    };
}
