// BUILD: add_benchmark(ppm=omp_parallel)

#include <rosetta.h>


static void kernel(pbsize_t n,
                   real alpha, real beta,
                   multarray<real, 2> A,
                   multarray<real, 2> B,
                   real tmp[],
                   real x[],
                   real y[]) {

#pragma omp parallel for schedule(static) default(none) firstprivate(n, alpha, beta, A, B, tmp, x, y)
  for (idx_t i = 0; i < n; i++) {
    tmp[i] = 0;
    y[i] = 0;
    for (idx_t j = 0; j < n; j++) {
      tmp[i] += A[i][j] * x[j];
      y[i] += B[i][j] * x[j];
    }
    y[i] = alpha * tmp[i] + beta * y[i];
  }
}



void run(State &state, pbsize_t n) {
  real alpha = 1.5;
  real beta = 1.2;
  auto A = state.allocate_array<double>({n, n}, /*fakedata*/ true, /*verify*/ false, "A");
  auto B = state.allocate_array<double>({n, n}, /*fakedata*/ true, /*verify*/ false, "B");
  auto tmp = state.allocate_array<double>({n}, /*fakedata*/ false, /*verify*/ false, "tmp");
  auto x = state.allocate_array<double>({n}, /*fakedata*/ true, /*verify*/ false, "x");
  auto y = state.allocate_array<double>({n}, /*fakedata*/ false, /*verify*/ true, "y");



  for (auto &&_ : state)
    kernel(n, alpha, beta, A, B, tmp, x, y);
}
