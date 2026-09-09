package models

// AlgoRequest rappresenta la richiesta inviata dal frontend al middleware
type AlgoRequest struct {
	Algorithm        string `json:"algorithm"`
	Data             []int  `json:"data"`
	Mode             string `json:"mode"`   // "steps" | "benchmark" | "benchmark_curve"
	Target           int    `json:"target"` // per search algorithms
	N                int    `json:"n"`      // per benchmark: dimensione array
	Runs             int    `json:"runs"`   // per benchmark: numero run (default 30)
	DataStructure    string `json:"data_structure"`
	DataDistribution string `json:"data_distribution"`
	StartN           int    `json:"start_n"`
	EndN             int    `json:"end_n"`
	StepN            int    `json:"step_n"`
}

// MemVar rappresenta una variabile locale nello stack frame
type MemVar map[string]string

// MemFrame rappresenta un frame sullo stack simulato
type MemFrame struct {
	Name string `json:"name"`
	Vars MemVar `json:"vars"`
}

// HeapBlock rappresenta un blocco allocato sull'heap simulato
type HeapBlock struct {
	Label   string `json:"label"`
	Size    int    `json:"size"`
	Content string `json:"content"`
}

// MemSnap rappresenta uno snapshot completo della memoria
type MemSnap struct {
	Stack []MemFrame  `json:"stack"`
	Heap  []HeapBlock `json:"heap"`
}

// StepEvent rappresenta un singolo passo dell'algoritmo
type StepEvent struct {
	Step        int     `json:"step"`
	Array       []int   `json:"array"`
	Highlight   []int   `json:"highlight"`
	Comparisons int     `json:"comparisons"`
	Swaps       int     `json:"swaps"`
	Memory      MemSnap `json:"memory"`
}

// ComplexityInfo descrive la complessità dell'algoritmo
type ComplexityInfo struct {
	Time  string `json:"time"`
	Space string `json:"space"`
}

// StepsResponse è la risposta del backend in mode="steps"
type StepsResponse struct {
	Status     string         `json:"status"`
	Steps      []StepEvent    `json:"steps"`
	Complexity ComplexityInfo `json:"complexity"`
}

// BenchStats sono le statistiche di benchmark
type BenchStats struct {
	MeanNs     float64   `json:"mean_ns"`
	MedianNs   float64   `json:"median_ns"`
	Q1Ns       float64   `json:"q1_ns"`
	Q3Ns       float64   `json:"q3_ns"`
	StdDevNs   float64   `json:"std_dev_ns"`
	RunTimesNs []float64 `json:"run_times_ns"`
}

// BenchResponse è la risposta del backend in mode="benchmark"
type BenchResponse struct {
	Status    string     `json:"status"`
	Algorithm string     `json:"algorithm"`
	N         int        `json:"n"`
	Runs      int        `json:"runs"`
	Stats     BenchStats `json:"stats"`
}

// CurveResponse è la risposta del backend in mode="benchmark_curve"
type CurveResponse struct {
	Status string          `json:"status"`
	Curve  []BenchResponse `json:"curve"`
}

// ErrorResponse è la risposta in caso di errore
type ErrorResponse struct {
	Status  string `json:"status"`
	Message string `json:"message"`
}

// AlgorithmInfo descrive un algoritmo disponibile
type AlgorithmInfo struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Category  string `json:"category"`
	TimeComp  string `json:"time_complexity"`
	SpaceComp string `json:"space_complexity"`
}
