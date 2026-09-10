#include "benchmark.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <numeric>
#include <random>
#include <stdexcept>

// -----------------------------------------------------------------------
// BenchmarkResult: run() — esegue l'algoritmo N volte con seed diversi
// -----------------------------------------------------------------------

BenchmarkResult Benchmarker::run(const std::string &algoName,
                                 std::function<void(int *, int)> algoFn, int n,
                                 int runs, const std::string &dataStructure,
                                 const std::string &dataDistribution) {
  if (n <= 0 || runs <= 0) {
    throw std::invalid_argument("n e runs devono essere > 0");
  }

  std::vector<double> times;
  times.reserve(runs);

  // Esecuzione sequenziale: un run alla volta, seed da 0 a runs-1
  for (int r = 0; r < runs; ++r) {
    auto data = generateData(n, static_cast<unsigned int>(r), dataDistribution);

    auto t0 = std::chrono::high_resolution_clock::now();
    auto t1 = t0;

    if (dataStructure == "heap") {
      int *arr = new int[n];
      std::copy(data.begin(), data.end(), arr);
      t0 = std::chrono::high_resolution_clock::now();
      algoFn(arr, n);
      t1 = std::chrono::high_resolution_clock::now();
      delete[] arr;
    } else if (dataStructure == "stack") {
      // VLA non è standard C++; usiamo std::vector ma misuriamo solo l'algoritmo
      std::vector<int> stackSim(data);
      int *arr = stackSim.data();
      t0 = std::chrono::high_resolution_clock::now();
      algoFn(arr, n);
      t1 = std::chrono::high_resolution_clock::now();
    } else {
      // vector (default)
      std::vector<int> v = data;
      t0 = std::chrono::high_resolution_clock::now();
      algoFn(v.data(), n);
      t1 = std::chrono::high_resolution_clock::now();
    }

    double elapsed_ns = static_cast<double>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0).count());
    times.push_back(elapsed_ns);
  }

  // Calcolo statistiche
  double mean = std::accumulate(times.begin(), times.end(), 0.0) / times.size();

  auto sorted = times;
  std::sort(sorted.begin(), sorted.end());

  double median = calcMedian(times); // copia interna
  double q1 = calcQuantile(sorted, 0.25);
  double q3 = calcQuantile(sorted, 0.75);
  double std_dev = calcStdDev(times, mean);

  BenchmarkResult result;
  result.algorithm = algoName;
  result.n = n;
  result.runs = runs;
  result.mean_ns = mean;
  result.median_ns = median;
  result.q1_ns = q1;
  result.q3_ns = q3;
  result.std_dev_ns = std_dev;
  result.run_times_ns = times;
  return result;
}

// -----------------------------------------------------------------------
// Helpers privati
// -----------------------------------------------------------------------

std::vector<int> Benchmarker::generateData(int n, unsigned int seed,
                                           const std::string &distType) {
  std::mt19937 rng(seed);
  std::vector<int> data(n);

  if (distType == "sorted") {
    for (int i = 0; i < n; ++i)
      data[i] = i;
  } else if (distType == "reversed") {
    for (int i = 0; i < n; ++i)
      data[i] = n - i;
  } else if (distType == "nearly_sorted") {
    for (int i = 0; i < n; ++i)
      data[i] = i;
    // scambia il 5% degli elementi
    std::uniform_int_distribution<int> dist(0, n - 1);
    int swaps = std::max(1, (int)(n * 0.05));
    for (int i = 0; i < swaps; ++i) {
      std::swap(data[dist(rng)], data[dist(rng)]);
    }
  } else {
    // random default
    std::uniform_int_distribution<int> dist(0, n * 10);
    for (auto &x : data) {
      x = dist(rng);
    }
  }
  return data;
}

double Benchmarker::calcMedian(std::vector<double> vals) {
  std::sort(vals.begin(), vals.end());
  size_t n = vals.size();
  if (n % 2 == 0) {
    return (vals[n / 2 - 1] + vals[n / 2]) / 2.0;
  }
  return vals[n / 2];
}

double Benchmarker::calcQuantile(const std::vector<double> &sorted, double q) {
  if (sorted.empty())
    return 0.0;
  double pos = q * (static_cast<double>(sorted.size()) - 1.0);
  size_t lo = static_cast<size_t>(std::floor(pos));
  size_t hi = static_cast<size_t>(std::ceil(pos));
  if (lo == hi)
    return sorted[lo];
  double frac = pos - static_cast<double>(lo);
  return sorted[lo] * (1.0 - frac) + sorted[hi] * frac;
}

double Benchmarker::calcStdDev(const std::vector<double> &vals, double mean) {
  double sq_sum = 0.0;
  for (double v : vals) {
    sq_sum += (v - mean) * (v - mean);
  }
  return std::sqrt(sq_sum / static_cast<double>(vals.size()));
}
