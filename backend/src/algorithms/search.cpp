#include "algorithms/search.hpp"
#include "algorithms/sorting.hpp"
#include <string>

// -----------------------------------------------------------------------
// Helper locale (reusa emitStep di sorting.cpp ma lho ridefinita qui)
// -----------------------------------------------------------------------

static void emitSearchStep(int& stepCount, int& comparisons,
                            const std::vector<int>& arr,
                            const std::vector<int>& highlight,
                            MemoryTracer& mem, const StepCallback& cb) {
    StepEvent ev;
    ev.step        = stepCount++;
    ev.array       = arr;
    ev.highlight   = highlight;
    ev.comparisons = comparisons;
    ev.swaps       = 0;
    ev.memory      = mem.snapshot();
    cb(ev);
}

// -----------------------------------------------------------------------
// Linear Search — O(n)
// -----------------------------------------------------------------------

int linearSearch(const std::vector<int>& arr, int target,
                 MemoryTracer& mem, StepCallback cb) {
    int n = static_cast<int>(arr.size());
    int step = 0, cmp = 0;

    mem.pushFrame("linearSearch", {{"n", std::to_string(n)},
                                    {"target", std::to_string(target)},
                                    {"i", "0"}});
    emitSearchStep(step, cmp, arr, {}, mem, cb);

    for (int i = 0; i < n; ++i) {
        ++cmp;
        mem.updateFrame({{"i", std::to_string(i)},
                          {"arr[i]", std::to_string(arr[i])}});
        emitSearchStep(step, cmp, arr, {i}, mem, cb);

        if (arr[i] == target) {
            emitSearchStep(step, cmp, arr, {i}, mem, cb); // trovato
            mem.popFrame();
            return i;
        }
    }
    emitSearchStep(step, cmp, arr, {}, mem, cb); // non trovato
    mem.popFrame();
    return -1;
}

// -----------------------------------------------------------------------
// Binary Search — O(log n) — arr deve essere ordinato
// -----------------------------------------------------------------------

int binarySearch(const std::vector<int>& arr, int target,
                 MemoryTracer& mem, StepCallback cb) {
    int n   = static_cast<int>(arr.size());
    int lo  = 0;
    int hi  = n - 1;
    int step = 0, cmp = 0;

    mem.pushFrame("binarySearch", {{"n", std::to_string(n)},
                                    {"target", std::to_string(target)},
                                    {"lo", "0"},
                                    {"hi", std::to_string(hi)}});
    emitSearchStep(step, cmp, arr, {}, mem, cb);

    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        ++cmp;
        mem.updateFrame({{"lo", std::to_string(lo)},
                          {"hi", std::to_string(hi)},
                          {"mid", std::to_string(mid)},
                          {"arr[mid]", std::to_string(arr[mid])}});
        emitSearchStep(step, cmp, arr, {lo, mid, hi}, mem, cb);

        if (arr[mid] == target) {
            emitSearchStep(step, cmp, arr, {mid}, mem, cb);
            mem.popFrame();
            return mid;
        } else if (arr[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    emitSearchStep(step, cmp, arr, {}, mem, cb); 
    mem.popFrame();
    return -1;
}

// =======================================================================
// VERSIONI PURE PER BENCHMARK 
// =======================================================================

int linearSearchBench(const int* arr, int n, int target) {
    for (int i = 0; i < n; ++i) {
        if (arr[i] == target) return i;
    }
    return -1;
}

int binarySearchBench(const int* arr, int n, int target) {
    int lo = 0, hi = n - 1;
    while (lo <= hi) {
        int mid = lo + (hi - lo) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) lo = mid + 1;
        else hi = mid - 1;
    }
    return -1;
}
