package handlers

import (
	"encoding/json"
	"net/http"

	"apl_middleware/models"
	"apl_middleware/worker"
)

// pool globale — inizializzato in main.go
var Pool *worker.Pool

// setCORSHeaders aggiunge gli header per permettere richieste dal frontend Python
func setCORSHeaders(w http.ResponseWriter) {
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.Header().Set("Content-Type", "application/json")
}

// sendError scrive una risposta di errore in JSON
func sendError(w http.ResponseWriter, code int, msg string) {
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(models.ErrorResponse{
		Status:  "error",
		Message: msg,
	})
}

// RunAlgorithm gestisce POST /api/run
// Riceve { algorithm, data, mode="steps" } e ritorna gli step dell'algoritmo
func RunAlgorithm(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w)

	// Gestione preflight CORS
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	if r.Method != http.MethodPost {
		sendError(w, http.StatusMethodNotAllowed, "solo POST è supportato")
		return
	}

	// Decodifica la richiesta JSON
	var req models.AlgoRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, http.StatusBadRequest, "JSON non valido: "+err.Error())
		return
	}
	req.Mode = "steps"

	// Invia al Worker Pool e attende la risposta tramite channel
	replyCh := Pool.Submit(req)
	result := <-replyCh

	if result.Err != nil {
		sendError(w, http.StatusInternalServerError, result.Err.Error())
		return
	}

	_ = json.NewEncoder(w).Encode(result.StepsResp)
}

// GetBenchmark gestisce POST /api/benchmark
// Riceve { algorithm, n, runs } e ritorna le statistiche di benchmark
func GetBenchmark(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	if r.Method != http.MethodPost {
		sendError(w, http.StatusMethodNotAllowed, "solo POST è supportato")
		return
	}

	var req models.AlgoRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, http.StatusBadRequest, "JSON non valido: "+err.Error())
		return
	}
	req.Mode = "benchmark"
	if req.Runs == 0 {
		req.Runs = 30
	}

	// Invia al Worker Pool e attende la risposta
	replyCh := Pool.Submit(req)
	result := <-replyCh

	if result.Err != nil {
		sendError(w, http.StatusInternalServerError, result.Err.Error())
		return
	}

	_ = json.NewEncoder(w).Encode(result.BenchResp)
}

// GetBenchmarkCurve gestisce POST /api/benchmark_curve
func GetBenchmarkCurve(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	if r.Method != http.MethodPost {
		sendError(w, http.StatusMethodNotAllowed, "solo POST è supportato")
		return
	}

	var req models.AlgoRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendError(w, http.StatusBadRequest, "JSON non valido: "+err.Error())
		return
	}
	req.Mode = "benchmark_curve"
	if req.Runs == 0 {
		req.Runs = 30
	}

	replyCh := Pool.Submit(req)
	result := <-replyCh

	if result.Err != nil {
		sendError(w, http.StatusInternalServerError, result.Err.Error())
		return
	}

	_ = json.NewEncoder(w).Encode(result.CurveResp)
}

// ListAlgorithms gestisce GET /api/algorithms
// Ritorna la lista degli algoritmi disponibili
func ListAlgorithms(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w)

	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	algorithms := []models.AlgorithmInfo{
		{ID: "bubble_sort", Name: "Bubble Sort", Category: "sorting", TimeComp: "O(n²)", SpaceComp: "O(1)"},
		{ID: "insertion_sort", Name: "Insertion Sort", Category: "sorting", TimeComp: "O(n²)", SpaceComp: "O(1)"},
		{ID: "selection_sort", Name: "Selection Sort", Category: "sorting", TimeComp: "O(n²)", SpaceComp: "O(1)"},
		{ID: "merge_sort", Name: "Merge Sort", Category: "sorting", TimeComp: "O(n log n)", SpaceComp: "O(n)"},
		{ID: "quick_sort", Name: "Quick Sort", Category: "sorting", TimeComp: "O(n log n)", SpaceComp: "O(log n)"},
		{ID: "linear_search", Name: "Linear Search", Category: "search", TimeComp: "O(n)", SpaceComp: "O(1)"},
		{ID: "binary_search", Name: "Binary Search", Category: "search", TimeComp: "O(log n)", SpaceComp: "O(1)"},
		{ID: "dijkstra", Name: "Dijkstra (Cammini)", Category: "graphs", TimeComp: "O(V²)", SpaceComp: "O(V)"},
	}

	_ = json.NewEncoder(w).Encode(algorithms)
}
