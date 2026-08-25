"""
Modelli dati per la comunicazione con il middleware Go.
Usa @dataclass per una struttura chiara e type hints come da lezione.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class MemVar:
    """Variabile locale all'interno di un frame dello stack."""
    name: str
    value: str


@dataclass
class MemFrame:
    """Frame di una chiamata di funzione sullo stack simulato."""
    name: str
    vars: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> MemFrame:
        return cls(name=d.get("name", ""), vars=d.get("vars", {}))


@dataclass
class HeapBlock:
    """Blocco allocato sull'heap simulato."""
    label: str
    size: int
    content: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> HeapBlock:
        return cls(label=d.get("label", ""), size=d.get("size", 0), content=d.get("content", ""))


@dataclass
class MemorySnapshot:
    """Snapshot completo di Stack e Heap in un dato istante."""
    stack: list[MemFrame] = field(default_factory=list)
    heap: list[HeapBlock] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> MemorySnapshot:
        stack = [MemFrame.from_dict(f) for f in d.get("stack", [])]
        heap  = [HeapBlock.from_dict(b) for b in d.get("heap", [])]
        return cls(stack=stack, heap=heap)


@dataclass
class StepEvent:
    """Un singolo passo dell'algoritmo."""
    step: int
    array: list[int]
    highlight: list[int]
    comparisons: int
    swaps: int
    memory: MemorySnapshot

    @classmethod
    def from_dict(cls, d: dict) -> StepEvent:
        return cls(
            step        = d.get("step", 0),
            array       = d.get("array", []),
            highlight   = d.get("highlight", []),
            comparisons = d.get("comparisons", 0),
            swaps       = d.get("swaps", 0),
            memory      = MemorySnapshot.from_dict(d.get("memory", {})),
        )


@dataclass
class ComplexityInfo:
    """Informazioni sulla complessità algoritmica."""
    time: str
    space: str

    @classmethod
    def from_dict(cls, d: dict) -> ComplexityInfo:
        return cls(time=d.get("time", "?"), space=d.get("space", "?"))


@dataclass
class AlgoResult:
    """Risultato completo di un'esecuzione step-by-step."""
    status: str
    steps: list[StepEvent]
    complexity: ComplexityInfo

    @classmethod
    def from_dict(cls, d: dict) -> AlgoResult:
        steps      = [StepEvent.from_dict(s) for s in d.get("steps", [])]
        complexity = ComplexityInfo.from_dict(d.get("complexity", {}))
        return cls(status=d.get("status", "error"), steps=steps, complexity=complexity)


@dataclass
class BenchStats:
    """Statistiche di benchmark."""
    mean_ns: float
    median_ns: float
    q1_ns: float
    q3_ns: float
    std_dev_ns: float
    run_times_ns: list[float] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> BenchStats:
        return cls(
            mean_ns      = d.get("mean_ns", 0.0),
            median_ns    = d.get("median_ns", 0.0),
            q1_ns        = d.get("q1_ns", 0.0),
            q3_ns        = d.get("q3_ns", 0.0),
            std_dev_ns   = d.get("std_dev_ns", 0.0),
            run_times_ns = d.get("run_times_ns", []),
        )


@dataclass
class BenchmarkResult:
    """Risultato completo di un benchmark."""
    status: str
    algorithm: str
    n: int
    runs: int
    stats: BenchStats

    @classmethod
    def from_dict(cls, d: dict) -> BenchmarkResult:
        return cls(
            status    = d.get("status", "error"),
            algorithm = d.get("algorithm", ""),
            n         = d.get("n", 0),
            runs      = d.get("runs", 0),
            stats     = BenchStats.from_dict(d.get("stats", {})),
        )


@dataclass
class AlgorithmInfo:
    """Descrizione di un algoritmo disponibile."""
    id: str
    name: str
    category: str
    time_complexity: str
    space_complexity: str

    @classmethod
    def from_dict(cls, d: dict) -> AlgorithmInfo:
        return cls(
            id               = d.get("id", ""),
            name             = d.get("name", ""),
            category         = d.get("category", ""),
            time_complexity  = d.get("time_complexity", "?"),
            space_complexity = d.get("space_complexity", "?"),
        )

@dataclass
class CurveResponse:
    status: str
    curve: list[BenchmarkResult]

    @classmethod
    def from_dict(cls, d: dict) -> CurveResponse:
        curve = [BenchmarkResult.from_dict(b) for b in d.get("curve", [])]
        return cls(status=d.get("status", "error"), curve=curve)
