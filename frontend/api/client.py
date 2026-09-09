"""
Client HTTP per comunicare con il middleware Go.
"""
from __future__ import annotations
import requests
from requests.exceptions import RequestException

from models.types import (
    AlgoResult, BenchmarkResult, AlgorithmInfo
)


class APIClient:
    """
    Client per il middleware Go (http://localhost:8080).
    Incapsula tutte le chiamate HTTP verso le API.
    """

    def __init__(self, base_url: str = "http://localhost:8080") -> None:
        self.base_url = base_url.rstrip("/")

    def _post(self, endpoint: str, payload: dict) -> dict:
        try:
            resp = requests.post(
                f"{self.base_url}{endpoint}",
                json=payload,
                timeout=60,  # timeout 60s per benchmark lunghi
            )
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            raise ConnectionError(f"Errore comunicazione con il middleware: {e}") from e

    def _get(self, endpoint: str) -> dict | list:
        try:
            resp = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except RequestException as e:
            raise ConnectionError(f"Errore comunicazione con il middleware: {e}") from e

    # ------------------------------------------------------------------
    # API 
    # ------------------------------------------------------------------

    def run_algorithm(self,
                      algo: str,
                      data: list[int],
                      target: int = 0) -> AlgoResult:
        """
        Esegue un algoritmo e ritorna tutti gli step.

        Args:
            algo:   ID dell'algoritmo (es. "bubble_sort")
            data:   array di interi su cui operare
            target: elemento da cercare (per algoritmi di ricerca)

        Returns:
            AlgoResult con la lista completa degli step
        """
        payload = {
            "algorithm": algo,
            "data":      data,
            "mode":      "steps",
            "target":    target,
        }
        raw = self._post("/api/run", payload)
        return AlgoResult.from_dict(raw)

    def get_benchmark(self,
                      algo: str,
                      n: int,
                      runs: int = 30,
                      data_structure: str = "vector",
                      data_distribution: str = "random") -> BenchmarkResult:
        """
        Esegue il benchmark di un algoritmo su N elementi per `runs` run.
        """
        payload = {
            "algorithm": algo,
            "data":      [],  
            "mode":      "benchmark",
            "n":         n,
            "runs":      runs,
            "data_structure": data_structure,
            "data_distribution": data_distribution,
        }
        raw = self._post("/api/benchmark", payload)
        return BenchmarkResult.from_dict(raw)

    def get_benchmark_curve(self, algo: str, start_n: int, end_n: int, step_n: int, runs: int = 30, data_structure: str = "vector", data_distribution: str = "random") -> CurveResponse:
        payload = {
            "algorithm": algo,
            "mode": "benchmark_curve",
            "start_n": start_n,
            "end_n": end_n,
            "step_n": step_n,
            "runs": runs,
            "data_structure": data_structure,
            "data_distribution": data_distribution
        }
        from models.types import CurveResponse
        raw = self._post("/api/benchmark_curve", payload)
        return CurveResponse.from_dict(raw)

    def list_algorithms(self) -> list[AlgorithmInfo]:
        """
        Ritorna la lista degli algoritmi disponibili.

        Returns:
            Lista di AlgorithmInfo
        """
        raw = self._get("/api/algorithms")
        return [AlgorithmInfo.from_dict(d) for d in raw]

    def health_check(self) -> bool:
        """Verifica che il middleware sia raggiungibile. Ritorna True (200) se OK."""
        try:
            resp = requests.get(f"{self.base_url}/api/health", timeout=3)
            return resp.status_code == 200
        except RequestException:
            return False
