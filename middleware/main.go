package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"

	"apl_middleware/handlers"
	"apl_middleware/runner"
	"apl_middleware/worker"
)

func main() {
	// Parametri configurabili da riga di comando
	port       := flag.String("port", "8080", "porta del server HTTP")
	backendPath := flag.String("backend", "backend.exe", "percorso dell'eseguibile C++")
	workers    := flag.Int("workers", 4, "numero di worker goroutine nel pool")
	flag.Parse()

	// Configura il path del backend C++
	runner.BackendPath = *backendPath

	// Inizializza il Worker Pool
	handlers.Pool = worker.NewPool(*workers)
	defer handlers.Pool.Shutdown()

	// Registra le route HTTP
	http.HandleFunc("/api/run",        handlers.RunAlgorithm)
	http.HandleFunc("/api/benchmark",  handlers.GetBenchmark)
	http.HandleFunc("/api/benchmark_curve", handlers.GetBenchmarkCurve)
	http.HandleFunc("/api/algorithms", handlers.ListAlgorithms)

	// Health check
	http.HandleFunc("/api/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		fmt.Fprintln(w, `{"status":"ok","service":"APL Middleware"}`)
	})

	addr := ":" + *port
	log.Printf("APL Middleware avviato su http://localhost%s", addr)
	log.Printf("Backend C++: %s", *backendPath)
	log.Printf("Worker goroutine: %d", *workers)
	log.Fatal(http.ListenAndServe(addr, nil))
}
