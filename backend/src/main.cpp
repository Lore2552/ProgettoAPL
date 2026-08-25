#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <map>
#include <stdexcept>
#include <functional>

#include "memory_tracer.hpp"
#include "benchmark.hpp"
#include "algorithms/sorting.hpp"
#include "algorithms/search.hpp"
#include "algorithms/graphs.hpp"
#include <cmath>

// ============================================================
// Mini JSON serializer/parser (nessuna dipendenza esterna)
// ============================================================

// --- Serializzazione ---

static std::string jsonStr(const std::string& s) {
    std::string out = "\"";
    for (char c : s) {
        if      (c == '"')  out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else                out += c;
    }
    return out + "\"";
}

static std::string toJson(const MemFrame& f) {
    std::string out = "{\"name\":" + jsonStr(f.func_name) + ",\"vars\":{";
    bool first = true;
    for (const auto& [k, v] : f.vars) {
        if (!first) out += ",";
        out += jsonStr(k) + ":" + jsonStr(v);
        first = false;
    }
    return out + "}}";
}

static std::string toJson(const HeapBlock& b) {
    return "{\"label\":" + jsonStr(b.label) +
           ",\"size\":" + std::to_string(b.size) +
           ",\"content\":" + jsonStr(b.content) + "}";
}

static std::string toJson(const MemorySnapshot& snap) {
    std::string out = "{\"stack\":[";
    for (size_t i = 0; i < snap.stack.size(); ++i) {
        if (i > 0) out += ",";
        out += toJson(snap.stack[i]);
    }
    out += "],\"heap\":[";
    for (size_t i = 0; i < snap.heap.size(); ++i) {
        if (i > 0) out += ",";
        out += toJson(snap.heap[i]);
    }
    return out + "]}";
}

static std::string toJson(const StepEvent& ev) {
    std::string arr = "[";
    for (size_t i = 0; i < ev.array.size(); ++i) {
        if (i > 0) arr += ",";
        arr += std::to_string(ev.array[i]);
    }
    arr += "]";

    std::string hl = "[";
    for (size_t i = 0; i < ev.highlight.size(); ++i) {
        if (i > 0) hl += ",";
        hl += std::to_string(ev.highlight[i]);
    }
    hl += "]";

    return "{\"step\":" + std::to_string(ev.step) +
           ",\"array\":" + arr +
           ",\"highlight\":" + hl +
           ",\"comparisons\":" + std::to_string(ev.comparisons) +
           ",\"swaps\":" + std::to_string(ev.swaps) +
           ",\"memory\":" + toJson(ev.memory) + "}";
}

static std::string toJson(const BenchmarkResult& br) {
    std::string times = "[";
    for (size_t i = 0; i < br.run_times_ns.size(); ++i) {
        if (i > 0) times += ",";
        times += std::to_string(br.run_times_ns[i]);
    }
    times += "]";

    return "{\"algorithm\":" + jsonStr(br.algorithm) +
           ",\"n\":" + std::to_string(br.n) +
           ",\"runs\":" + std::to_string(br.runs) +
           ",\"stats\":{" +
               "\"mean_ns\":"   + std::to_string(br.mean_ns) +
               ",\"median_ns\":" + std::to_string(br.median_ns) +
               ",\"q1_ns\":"    + std::to_string(br.q1_ns) +
               ",\"q3_ns\":"    + std::to_string(br.q3_ns) +
               ",\"std_dev_ns\":" + std::to_string(br.std_dev_ns) +
               ",\"run_times_ns\":" + times +
           "}}";
}

// --- Mini parser ---
// Parsing minimale solo per i campi che ci servono

static std::string extractString(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\":\"";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return "";
    pos += search.size();
    size_t end = json.find('"', pos);
    if (end == std::string::npos) return "";
    return json.substr(pos, end - pos);
}

static std::vector<int> extractIntArray(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\":[";
    size_t pos = json.find(search);
    std::vector<int> result;
    if (pos == std::string::npos) return result;
    pos += search.size();
    size_t end = json.find(']', pos);
    if (end == std::string::npos) return result;
    std::string arr = json.substr(pos, end - pos);
    std::stringstream ss(arr);
    std::string token;
    while (std::getline(ss, token, ',')) {
        if (!token.empty()) {
            try { result.push_back(std::stoi(token)); }
            catch (...) {}
        }
    }
    return result;
}

static int extractInt(const std::string& json, const std::string& key, int def = 30) {
    std::string search = "\"" + key + "\":";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return def;
    pos += search.size();
    size_t end = pos;
    while (end < json.size() && (std::isdigit(json[end]) || json[end] == '-')) ++end;
    try { return std::stoi(json.substr(pos, end - pos)); }
    catch (...) { return def; }
}

// ============================================================
// Dispatch algoritmo
// ============================================================

struct AlgorithmInfo {
    std::string time_complexity;
    std::string space_complexity;
};

static AlgorithmInfo getInfo(const std::string& algo) {
    static const std::map<std::string, AlgorithmInfo> info = {
        {"bubble_sort",    {"O(n^2)",    "O(1)"}},
        {"insertion_sort", {"O(n^2)",    "O(1)"}},
        {"selection_sort", {"O(n^2)",    "O(1)"}},
        {"merge_sort",     {"O(n log n)","O(n)"}},
        {"quick_sort",     {"O(n log n)","O(log n)"}},
        {"linear_search",  {"O(n)",      "O(1)"}},
        {"binary_search",  {"O(log n)",  "O(1)"}},
        {"dijkstra",       {"O(V^2)",    "O(V)"}},
    };
    auto it = info.find(algo);
    if (it != info.end()) return it->second;
    return {"O(?)", "O(?)"};
}

// ============================================================
// Main — legge JSON da stdin, scrive JSON su stdout
// ============================================================

int main() {
    // Leggi tutto stdin (il middleware chiude il pipe dopo aver inviato il JSON)
    std::string input((std::istreambuf_iterator<char>(std::cin)),
                       std::istreambuf_iterator<char>());

    try {
        std::string algo = extractString(input, "algorithm");
        std::string mode = extractString(input, "mode");
        std::vector<int> data = extractIntArray(input, "data");
        int runs = extractInt(input, "runs", 30);
        int n    = extractInt(input, "n", static_cast<int>(data.size()));

        if (algo.empty()) {
            std::cout << "{\"status\":\"error\",\"message\":\"campo 'algorithm' mancante\"}\n";
            return 1;
        }

        // ---- MODE: steps ----
        if (mode == "steps" || mode.empty()) {
            if (data.empty()) {
                std::cout << "{\"status\":\"error\",\"message\":\"campo 'data' vuoto\"}\n";
                return 1;
            }

            MemoryTracer mem;
            std::vector<StepEvent> steps;
            StepCallback cb = [&steps](const StepEvent& ev){ steps.push_back(ev); };

            if      (algo == "bubble_sort")    bubbleSort(data, mem, cb);
            else if (algo == "insertion_sort") insertionSort(data, mem, cb);
            else if (algo == "selection_sort") selectionSort(data, mem, cb);
            else if (algo == "merge_sort")     mergeSort(data, mem, cb);
            else if (algo == "quick_sort")     quickSort(data, mem, cb);
            else if (algo == "linear_search") {
                int target = extractInt(input, "target", 0);
                linearSearch(data, target, mem, cb);
            }
            else if (algo == "binary_search") {
                int target = extractInt(input, "target", 0);
                // binary search richiede array ordinato
                std::sort(data.begin(), data.end());
                binarySearch(data, target, mem, cb);
            }
            else if (algo == "dijkstra") {
                int start_node = extractInt(input, "start_node", 0);
                dijkstra(data, start_node, mem, cb);
            }
            else {
                std::cout << "{\"status\":\"error\",\"message\":\"algoritmo non riconosciuto: "
                          + algo + "\"}\n";
                return 1;
            }

            // Serializza risposta
            auto info = getInfo(algo);
            std::string out = "{\"status\":\"ok\",\"steps\":[";
            for (size_t i = 0; i < steps.size(); ++i) {
                if (i > 0) out += ",";
                out += toJson(steps[i]);
            }
            out += "],\"complexity\":{\"time\":" + jsonStr(info.time_complexity) +
                   ",\"space\":" + jsonStr(info.space_complexity) + "}}";
            std::cout << out << "\n";
        }

        // ---- MODE: benchmark ----
        else if (mode == "benchmark") {
            if (n <= 0) n = static_cast<int>(data.size());
            if (n <= 0) n = 100;

            std::string dataStruct = extractString(input, "data_structure");
            if (dataStruct.empty()) dataStruct = "vector";
            std::string dataDist = extractString(input, "data_distribution");
            if (dataDist.empty()) dataDist = "random";

            Benchmarker bm;
            BenchmarkResult result;

            auto makeAlgoFn = [&](const std::string& a) -> std::function<void(int*, int)> {
                return [a](int* arr, int sz) {
                    if      (a == "bubble_sort")    bubbleSortBench(arr, sz);
                    else if (a == "insertion_sort") insertionSortBench(arr, sz);
                    else if (a == "selection_sort") selectionSortBench(arr, sz);
                    else if (a == "merge_sort")     mergeSortBench(arr, sz);
                    else if (a == "quick_sort")     quickSortBench(arr, sz);
                    else if (a == "linear_search") {
                        linearSearchBench(arr, sz, arr[0]);
                    }
                    else if (a == "binary_search") {
                        std::sort(arr, arr + sz);
                        binarySearchBench(arr, sz, arr[sz/2]);
                    }
                    else if (a == "dijkstra") {
                        int nodes = static_cast<int>(std::sqrt(sz));
                        if (nodes * nodes == sz) dijkstraBench(arr, nodes, 0);
                    }
                };
            };

            if (algo == "bubble_sort"    || algo == "insertion_sort" ||
                algo == "selection_sort" || algo == "merge_sort"     ||
                algo == "quick_sort"     || algo == "linear_search"  ||
                algo == "binary_search"  || algo == "dijkstra") {
                result = bm.run(algo, makeAlgoFn(algo), n, runs, dataStruct, dataDist);
            } else {
                std::cout << "{\"status\":\"error\",\"message\":\"algoritmo non riconosciuto\"}\n";
                return 1;
            }

            std::cout << "{\"status\":\"ok\"," + toJson(result).substr(1) << "\n";
        }
        
        // ---- MODE: benchmark_curve ----
        else if (mode == "benchmark_curve") {
            int start_n = extractInt(input, "start_n", 1000);
            int end_n   = extractInt(input, "end_n", 10000);
            int step_n  = extractInt(input, "step_n", 1000);

            std::string dataStruct = extractString(input, "data_structure");
            if (dataStruct.empty()) dataStruct = "vector";
            std::string dataDist = extractString(input, "data_distribution");
            if (dataDist.empty()) dataDist = "random";

            Benchmarker bm;
            std::vector<BenchmarkResult> results;

            auto makeAlgoFn = [&](const std::string& a) -> std::function<void(int*, int)> {
                return [a](int* arr, int sz) {
                    if      (a == "bubble_sort")    bubbleSortBench(arr, sz);
                    else if (a == "insertion_sort") insertionSortBench(arr, sz);
                    else if (a == "selection_sort") selectionSortBench(arr, sz);
                    else if (a == "merge_sort")     mergeSortBench(arr, sz);
                    else if (a == "quick_sort")     quickSortBench(arr, sz);
                    else if (a == "linear_search")  linearSearchBench(arr, sz, arr[0]);
                    else if (a == "binary_search") {
                        std::sort(arr, arr + sz);
                        binarySearchBench(arr, sz, arr[sz/2]);
                    }
                    else if (a == "dijkstra") {
                        int nodes = static_cast<int>(std::sqrt(sz));
                        if (nodes * nodes == sz) dijkstraBench(arr, nodes, 0);
                    }
                };
            };

            for (int curr_n = start_n; curr_n <= end_n; curr_n += step_n) {
                if (algo == "bubble_sort"    || algo == "insertion_sort" ||
                    algo == "selection_sort" || algo == "merge_sort"     ||
                    algo == "quick_sort"     || algo == "linear_search"  ||
                    algo == "binary_search"  || algo == "dijkstra") {
                    results.push_back(bm.run(algo, makeAlgoFn(algo), curr_n, runs, dataStruct, dataDist));
                } else {
                    std::cout << "{\"status\":\"error\",\"message\":\"algoritmo non riconosciuto\"}\n";
                    return 1;
                }
            }

            std::string out = "{\"status\":\"ok\",\"curve\":[";
            for(size_t i = 0; i < results.size(); ++i) {
                if(i > 0) out += ",";
                out += toJson(results[i]);
            }
            out += "]}";
            std::cout << out << "\n";
        }

        else {
            std::cout << "{\"status\":\"error\",\"message\":\"mode non valida: " + mode + "\"}\n";
            return 1;
        }

    } catch (const std::exception& e) {
        std::cout << "{\"status\":\"error\",\"message\":" + jsonStr(e.what()) + "}\n";
        return 1;
    }

    return 0;
}
