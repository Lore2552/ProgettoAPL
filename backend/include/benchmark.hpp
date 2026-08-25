#pragma once
#include <vector>
#include <functional>
#include <string>

// -----------------------------------------------------------------------
// BenchmarkResult — risultato di N run di un algoritmo
// -----------------------------------------------------------------------

struct BenchmarkResult {
    std::string algorithm;
    int         n;          // dimensione dell'array
    int         runs;       // numero di esecuzioni
    double      mean_ns;
    double      median_ns;
    double      q1_ns;
    double      q3_ns;
    double      std_dev_ns;
    std::vector<double> run_times_ns; // tempi raw di ogni run
};

// -----------------------------------------------------------------------
// Benchmarker — misura i tempi di esecuzione di un algoritmo
// Usa std::chrono::high_resolution_clock per massima precisione
// -----------------------------------------------------------------------

class Benchmarker {
public:
    Benchmarker() = default;
    ~Benchmarker() = default;

    // Non copiabile
    Benchmarker(const Benchmarker&) = delete;
    Benchmarker& operator=(const Benchmarker&) = delete;

    /// Esegue algoFn per `runs` volte con array generati da seed diversi,
    /// di dimensione n. Ritorna le statistiche aggregate.
    /// algoFn riceve un std::vector<int> per valore (copia fresca ogni run)
    BenchmarkResult run(const std::string& algoName,
                        std::function<void(int*, int)> algoFn,
                        int n,
                        int runs = 30,
                        const std::string& dataStructure = "vector",
                        const std::string& dataDistribution = "random");

private:
    /// Genera un array con il seed dato e la distribuzione richiesta
    static std::vector<int> generateData(int n, unsigned int seed, const std::string& distType);

    /// Calcola mediana da un vettore di valori (modifica la copia)
    static double calcMedian(std::vector<double> vals);

    /// Calcola quartile (0.25 o 0.75) da un vettore ordinato
    static double calcQuantile(const std::vector<double>& sorted, double q);

    /// Calcola deviazione standard
    static double calcStdDev(const std::vector<double>& vals, double mean);
};
