package worker

import (
	"apl_middleware/models"
	"apl_middleware/runner"
	"sync"
)

// Job rappresenta un'unità di lavoro da eseguire
type Job struct {
	Request models.AlgoRequest
	ReplyCh chan<- Result
}

// Result contiene il risultato di un'esecuzione (steps o benchmark)
type Result struct {
	StepsResp *models.StepsResponse
	BenchResp *models.BenchResponse
	CurveResp *models.CurveResponse
	Err       error
}

// Pool gestisce un insieme di goroutine worker
type Pool struct {
	jobs chan Job
	wg   sync.WaitGroup
}

// NewPool crea un nuovo Pool con n worker goroutine
func NewPool(n int) *Pool {
	p := &Pool{
		jobs: make(chan Job, n*2), // buffer per evitare blocchi immediati
	}
	// Lancia n goroutine worker
	for i := 0; i < n; i++ {
		p.wg.Add(1)
		go p.worker()
	}
	return p
}

// worker è la goroutine interna che legge i job dal canale e li elabora
func (p *Pool) worker() {
	defer p.wg.Done()
	for job := range p.jobs {
		result := processJob(job.Request)
		job.ReplyCh <- result
	}
}

// Submit invia un job al pool e ritorna un canale da cui leggere il risultato
func (p *Pool) Submit(req models.AlgoRequest) <-chan Result {
	replyCh := make(chan Result, 1) // buffered: il worker non blocca
	p.jobs <- Job{
		Request: req,
		ReplyCh: replyCh,
	}
	return replyCh
}

// Shutdown chiude il pool e attende che tutti i worker terminino
func (p *Pool) Shutdown() {
	close(p.jobs)
	p.wg.Wait()
}

// processJob esegue il job chiamando il runner appropriato
func processJob(req models.AlgoRequest) Result {
	switch req.Mode {
	case "steps":
		resp, err := runner.RunSteps(req)
		return Result{StepsResp: resp, Err: err}
	case "benchmark":
		resp, err := runner.RunBenchmark(req)
		return Result{BenchResp: resp, Err: err}
	case "benchmark_curve":
		resp, err := runner.RunCurve(req)
		return Result{CurveResp: resp, Err: err}
	default:
		resp, err := runner.RunSteps(req)
		return Result{StepsResp: resp, Err: err}
	}
}
