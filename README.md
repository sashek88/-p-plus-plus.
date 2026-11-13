# -p-plus-plus.
P++ new python language compiler more faster and more easier 
# P++ (p-plus-plus)

> A high-performance, symbolic, zero-dependency compiler toolchain that auto-profiles host hardware to generate cache-tiled, SIMD-vectorized native C code safely.

---

## 🚀 Key Features

* **Hardware Auto-Discovery (`pp_hardware.py`):** Automatically detects CPU architecture, SIMD vector extensions (AVX2, AVX-512, ARM NEON), physical cores, and L1 cache boundaries.
* **Cache-Blocked Tiling (`pp_compiler.py`):** Dynamically computes optimal loop tile sizes to guarantee L1 data cache residency, paired with 64-byte memory alignment and OpenMP SIMD pragmas.
* **Metal-Level Safety:** Includes pre-flight thermal checks, memory pre-allocation bounds checking (capping workloads safely below system RAM limits), and execution watchdogs.
* **Unified CLI Controller (`ppp.py`):** Single entry point for compiling, executing, benchmarking, and auditing performance regressions.
* **Automated CI/CD:** Integrated GitHub Actions workflows for continuous integration testing across multiple Python versions and multi-platform binary releases.

---

## 🛠️ Project Architecture

```text
p-plus-plus/
├── pp_hardware.py    # Host hardware profiler & safety guardrails
├── pp_compiler.py    # Symbolic-to-C cache-blocked compiler emitter
├── ppp.py            # Unified master CLI controller (run, bench, audit)
├── pp_test.py        # Automated integration test suite
└── build.py          # Automated packaging script (PyInstaller binary builder)
