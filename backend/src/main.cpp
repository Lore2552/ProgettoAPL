#include <algorithm>
#include <cmath>
#include <functional>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

#include "algorithms/graphs.hpp"
#include "algorithms/search.hpp"
#include "algorithms/sorting.hpp"
#include "benchmark.hpp"
#include "json_utils.hpp"
#include "memory_tracer.hpp"

// ============================================================
// Dispatch algoritmo
// ============================================================

struct AlgorithmInfo {
  std::string time_complexity;
  std::string space_complexity;
};

static AlgorithmInfo getInfo(const std::string &algo) {
  static const std::map<std::string, AlgorithmInfo> info = {
      {"bubble_sort", {"O(n^2)", "O(1)"}},
      {"insertion_sort", {"O(n^2)", "O(1)"}},
      {"selection_sort", {"O(n^2)", "O(1)"}},
      {"merge_sort", {"O(n log n)", "O(n)"}},
      {"quick_sort", {"O(n log n)", "O(log n)"}},
      {"linear_search", {"O(n)", "O(1)"}},
      {"binary_search", {"O(log n)", "O(1)"}},
      {"dijkstra", {"O(V^2)", "O(V)"}},
  };
  auto it = info.find(algo);
  if (it != info.end())
    return it->second;
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
    auto input_json = json::parse(input);

    std::string algo = input_json.value("algorithm", std::string{});
    std::string mode = input_json.value("mode", std::string{});
    std::vector<int> data;
    if (input_json.contains("data") && input_json["data"].is_array()) {
      data = input_json["data"].get<std::vector<int>>();
    }
    int runs = input_json.value("runs", 30);
    int n = input_json.value("n", static_cast<int>(data.size()));

    if (algo.empty()) {
      std::cout << json{{"status", "error"},
                        {"message", "campo 'algorithm' mancante"}}
                       .dump()
                << "\n";
      return 1;
    }

    // ---- MODE: steps ----
    if (mode == "steps" || mode.empty()) {
      if (data.empty()) {
        std::cout << json{{"status", "error"},
                          {"message", "campo 'data' vuoto"}}
                         .dump()
                  << "\n";
        return 1;
      }

      MemoryTracer mem;
      std::vector<StepEvent> steps;
      StepCallback cb = [&steps](const StepEvent &ev) { steps.push_back(ev); };

      if (algo == "bubble_sort")
        bubbleSort(data, mem, cb);
      else if (algo == "insertion_sort")
        insertionSort(data, mem, cb);
      else if (algo == "selection_sort")
        selectionSort(data, mem, cb);
      else if (algo == "merge_sort")
        mergeSort(data, mem, cb);
      else if (algo == "quick_sort")
        quickSort(data, mem, cb);
      else if (algo == "linear_search") {
        int target = input_json.value("target", 0);
        linearSearch(data, target, mem, cb);
      } else if (algo == "binary_search") {
        int target = input_json.value("target", 0);
        // la ricerca binaria vuole un array ordinato
        std::sort(data.begin(), data.end());
        binarySearch(data, target, mem, cb);
      } else if (algo == "dijkstra") {
        int start_node = input_json.value("start_node", 0);
        dijkstra(data, start_node, mem, cb);
      } else {
        std::cout << json{{"status", "error"},
                          {"message", "algoritmo non riconosciuto: " + algo}}
                         .dump()
                  << "\n";
        return 1;
      }

      // Serializza risposta
      auto info = getInfo(algo);
      json response = {
          {"status", "ok"},
          {"steps", steps},
          {"complexity",
           {{"time", info.time_complexity}, {"space", info.space_complexity}}}};
      std::cout << response.dump() << "\n";
    }

    // ---- MODE: benchmark ----
    else if (mode == "benchmark") {
      if (n <= 0)
        n = static_cast<int>(data.size());
      if (n <= 0)
        n = 100;

      std::string dataStruct =
          input_json.value("data_structure", std::string{"vector"});
      std::string dataDist =
          input_json.value("data_distribution", std::string{"random"});

      Benchmarker bm;
      BenchmarkResult result;

      auto makeAlgoFn =
          [&](const std::string &a) -> std::function<void(int *, int)> {
        return [a](int *arr, int sz) {
          if (a == "bubble_sort")
            bubbleSortBench(arr, sz);
          else if (a == "insertion_sort")
            insertionSortBench(arr, sz);
          else if (a == "selection_sort")
            selectionSortBench(arr, sz);
          else if (a == "merge_sort")
            mergeSortBench(arr, sz);
          else if (a == "quick_sort")
            quickSortBench(arr, sz);
          else if (a == "linear_search") {
            linearSearchBench(arr, sz, arr[0]);
          } else if (a == "binary_search") {
            std::sort(arr, arr + sz);
            binarySearchBench(arr, sz, arr[sz / 2]);
          } else if (a == "dijkstra") {
            int nodes = static_cast<int>(std::sqrt(sz));
            if (nodes * nodes == sz)
              dijkstraBench(arr, nodes, 0);
          }
        };
      };

      if (algo == "bubble_sort" || algo == "insertion_sort" ||
          algo == "selection_sort" || algo == "merge_sort" ||
          algo == "quick_sort" || algo == "linear_search" ||
          algo == "binary_search" || algo == "dijkstra") {
        result = bm.run(algo, makeAlgoFn(algo), n, runs, dataStruct, dataDist);
      } else {
        std::cout << json{{"status", "error"},
                          {"message", "algoritmo non riconosciuto"}}
                         .dump()
                  << "\n";
        return 1;
      }

      // Merge status:"ok" con il BenchmarkResult serializzato
      json response = result;
      response["status"] = "ok";
      std::cout << response.dump() << "\n";
    }

    // ---- MODE: benchmark_curve ----
    else if (mode == "benchmark_curve") {
      int start_n = input_json.value("start_n", 1000);
      int end_n = input_json.value("end_n", 10000);
      int step_n = input_json.value("step_n", 1000);

      std::string dataStruct =
          input_json.value("data_structure", std::string{"vector"});
      std::string dataDist =
          input_json.value("data_distribution", std::string{"random"});

      Benchmarker bm;
      std::vector<BenchmarkResult> results;

      auto makeAlgoFn =
          [&](const std::string &a) -> std::function<void(int *, int)> {
        return [a](int *arr, int sz) {
          if (a == "bubble_sort")
            bubbleSortBench(arr, sz);
          else if (a == "insertion_sort")
            insertionSortBench(arr, sz);
          else if (a == "selection_sort")
            selectionSortBench(arr, sz);
          else if (a == "merge_sort")
            mergeSortBench(arr, sz);
          else if (a == "quick_sort")
            quickSortBench(arr, sz);
          else if (a == "linear_search")
            linearSearchBench(arr, sz, arr[0]);
          else if (a == "binary_search") {
            std::sort(arr, arr + sz);
            binarySearchBench(arr, sz, arr[sz / 2]);
          } else if (a == "dijkstra") {
            int nodes = static_cast<int>(std::sqrt(sz));
            if (nodes * nodes == sz)
              dijkstraBench(arr, nodes, 0);
          }
        };
      };

      for (int curr_n = start_n; curr_n <= end_n; curr_n += step_n) {
        if (algo == "bubble_sort" || algo == "insertion_sort" ||
            algo == "selection_sort" || algo == "merge_sort" ||
            algo == "quick_sort" || algo == "linear_search" ||
            algo == "binary_search" || algo == "dijkstra") {
          results.push_back(bm.run(algo, makeAlgoFn(algo), curr_n, runs,
                                   dataStruct, dataDist));
        } else {
          std::cout << json{{"status", "error"},
                            {"message", "algoritmo non riconosciuto"}}
                           .dump()
                    << "\n";
          return 1;
        }
      }

      json response = {{"status", "ok"}, {"curve", json::array()}};
      for (const auto &r : results) {
        json entry = r;
        entry["status"] = "ok";
        response["curve"].push_back(entry);
      }
      std::cout << response.dump() << "\n";
    }

    else {
      std::cout << json{{"status", "error"},
                        {"message", "mode non valida: " + mode}}
                       .dump()
                << "\n";
      return 1;
    }

  } catch (const std::exception &e) {
    std::cout << json{{"status", "error"}, {"message", e.what()}}.dump()
              << "\n";
    return 1;
  }

  return 0;
}
