// BUILD: add_benchmark(ppm=sycl)
#include <CL/sycl.hpp>
#include <rosetta.h>

using namespace cl::sycl;

void mykernel(queue q, buffer<real, 1> C_buf, buffer<real, 1> A_buf, buffer<real, 1> B_buf, pbsize_t n, pbsize_t m, real alpha, real beta) {
  q.submit([&](handler &cgh) {
    auto C1 = C_buf.get_access<access::mode::read_write>(cgh);
    auto A1 = A_buf.get_access<access::mode::read>(cgh);
    auto B1 = B_buf.get_access<access::mode::read>(cgh);

    cgh.parallel_for<class kernel1>(range<1>(n), [=](id<1> i) {
      for (idx_t j = 0; j <= i; j++)
        C1[i * n + j] *= beta;

      for (idx_t j = 0; j <= i; j++)
        for (idx_t k = 0; k < m; k++)
          C1[i * n + j] += A1[j * m + k] * alpha * B1[i * m + k] + B1[j * m + k] * alpha * A1[i * m + k];
    });
  });
}



void run(State &state, pbsize_t pbsize) {
  pbsize_t n = pbsize;
  pbsize_t m = pbsize - pbsize / 6;

  real alpha = 1.5;
  real beta = 1.2;
  auto C = state.allocate_array<double>({n, n}, /*fakedata*/ true, /*verify*/ true, "C");
  auto A = state.allocate_array<double>({n, m}, /*fakedata*/ true, /*verify*/ false, "A");
  auto B = state.allocate_array<double>({n, m}, /*fakedata*/ true, /*verify*/ false, "B");

  queue q(default_selector{});
  {
    buffer<real, 1> C_buf(C.data(), range<1>(n * n));
    buffer<real, 1> A_buf(A.data(), range<1>(n * m));
    buffer<real, 1> B_buf(B.data(), range<1>(n * m));
    for (auto &&_ : state) {
      mykernel(q, C_buf, A_buf, B_buf, n, m, alpha, beta);
    }
  }
}
