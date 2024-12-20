// BUILD: add_benchmark(ppm=sycl)
#include <CL/sycl.hpp>
#include <rosetta.h>

using namespace cl::sycl;

static void mykernel(queue q, buffer<real, 1> &res_Buf, pbsize_t n, pbsize_t n_rounded) {
  q.submit([&](handler &cgh) {
    auto sumr = reduction(res_Buf, cgh, plus<>());
    cgh.parallel_for<class reductionKernel>(nd_range<1>(n_rounded, 256), sumr,
                                            [=](nd_item<1> item, auto &sumr_arg) {
                                              idx_t i = item.get_global_id(0);
                                              if (i < n) {
                                                sumr_arg += i;
                                              }
                                            });
  });
  q.wait_and_throw();
}

void run(State &state, pbsize_t n) {
  auto sum_owner = state.allocate_array<real>({1}, /*fakedata*/ false, /*verify*/ true, "sum");

  pbsize_t n_rounded = (n + 255) / 256 * 256;

  queue q(default_selector{});
  {
    buffer<real, 1> sum_buf(sum_owner.data(), range<1>(1));
    for (auto &&_ : state) {
      {
        mykernel(q, sum_buf, n, n_rounded);
      }
    }
  }
}