package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os/exec"
	"time"

	"apl_middleware/models"
)

// BackendPath è il percorso dell'eseguibile C++
// Viene impostato all'avvio del server (vedi main.go)
var BackendPath = "backend.exe"

// RunCpp esegue il backend C++ con la richiesta data e ritorna la risposta grezza (JSON)
func RunCpp(req models.AlgoRequest) ([]byte, error) {
	// Serializza la richiesta in JSON
	reqJSON, err := json.Marshal(req)
	if err != nil {
		return nil, fmt.Errorf("errore serializzazione richiesta: %w", err)
	}

	// Timeout di 30 secondi per evitare blocchi
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Avvia il processo C++
	cmd := exec.CommandContext(ctx, BackendPath)
	cmd.Stdin = bytes.NewReader(reqJSON)

	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			return nil, fmt.Errorf("timeout: il backend C++ ha impiegato troppo")
		}
		return nil, fmt.Errorf("errore esecuzione backend: %w\nstderr: %s", err, stderr.String())
	}

	return stdout.Bytes(), nil
}

// RunSteps esegue il backend in modalità "steps" e ritorna la risposta deserializzata
func RunSteps(req models.AlgoRequest) (*models.StepsResponse, error) {
	req.Mode = "steps"
	raw, err := RunCpp(req)
	if err != nil {
		return nil, err
	}

	var resp models.StepsResponse
	if err := json.Unmarshal(raw, &resp); err != nil {
		return nil, fmt.Errorf("errore parsing risposta steps: %w\nraw: %s", err, string(raw))
	}
	if resp.Status != "ok" {
		// Prova a leggere come ErrorResponse
		var errResp models.ErrorResponse
		_ = json.Unmarshal(raw, &errResp)
		return nil, fmt.Errorf("backend error: %s", errResp.Message)
	}
	return &resp, nil
}

// RunBenchmark esegue il backend in modalità "benchmark" e ritorna la risposta
func RunBenchmark(req models.AlgoRequest) (*models.BenchResponse, error) {
	req.Mode = "benchmark"
	if req.Runs == 0 {
		req.Runs = 30
	}
	raw, err := RunCpp(req)
	if err != nil {
		return nil, err
	}

	var resp models.BenchResponse
	if err := json.Unmarshal(raw, &resp); err != nil {
		return nil, fmt.Errorf("errore parsing risposta benchmark: %w\nraw: %s", err, string(raw))
	}
	if resp.Status != "ok" {
		var errResp models.ErrorResponse
		_ = json.Unmarshal(raw, &errResp)
		return nil, fmt.Errorf("backend error: %s", errResp.Message)
	}
	return &resp, nil
}

// RunCurve esegue il backend in modalità "benchmark_curve"
func RunCurve(req models.AlgoRequest) (*models.CurveResponse, error) {
	req.Mode = "benchmark_curve"
	if req.Runs == 0 {
		req.Runs = 30
	}
	raw, err := RunCpp(req)
	if err != nil {
		return nil, err
	}

	var resp models.CurveResponse
	if err := json.Unmarshal(raw, &resp); err != nil {
		return nil, fmt.Errorf("errore parsing risposta curve: %w\nraw: %s", err, string(raw))
	}
	if resp.Status != "ok" {
		var errResp models.ErrorResponse
		_ = json.Unmarshal(raw, &errResp)
		return nil, fmt.Errorf("backend error: %s", errResp.Message)
	}
	return &resp, nil
}
