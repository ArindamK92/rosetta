// BUILD: add_benchmark(ppm=sycl,sources=[__file__,"ludcmp-common.cxx"])

#include "ludcmp-common.h"
#include <CL/sycl.hpp>
#include <rosetta.h>

using namespace cl::sycl;

void mykernel(queue &q, pbsize_t n, buffer<real, 1> &A_buf,
              buffer<real, 1> &b_buf, buffer<real, 1> &x_buf, buffer<real, 1> &y_buf) {

  real w = 0;
  buffer<real, 1> w_buf(&w, range<1>(1));
  for (idx_t i = 0; i < n; i++) {
    for (idx_t j = 0; j < i; j++) {
      q.submit([&](handler &cgh) {
        auto w_acc = w_buf.get_access<access::mode::read_write>(cgh);
        auto A_acc = A_buf.get_access<access::mode::read>(cgh);
        cgh.single_task<class initKernel1>([=]() {
          w_acc[0] = A_acc[i * n + j];
        });
      });
      pbsize_t j_rounded = (j + 255) / 256 * 256;
      if (j_rounded > 0) {
        q.submit([&](handler &cgh) {
          auto A_acc = A_buf.get_access<access::mode::read>(cgh);
          auto sumr = reduction(w_buf, cgh, plus<>());
          cgh.parallel_for<class reductionKernel1>(nd_range<1>(j_rounded, 256), sumr,
                                                   [=](nd_item<1> item, auto &sumr_arg) {
                                                     idx_t k = item.get_global_id(0);
                                                     if (k < j) {
                                                       sumr_arg += -A_acc[i * n + k] * A_acc[k * n + j];
                                                     }
                                                   });
        });
      }
      q.submit([&](handler &cgh) {
        auto w_acc = w_buf.get_access<access::mode::read>(cgh);
        auto A_acc = A_buf.get_access<access::mode::read_write>(cgh);
        cgh.single_task<class AKernel1>([=]() {
          A_acc[i * n + j] = w_acc[0] / A_acc[j * n + j];
        });
      });
    }

    for (idx_t j = i; j < n; j++) {
      q.submit([&](handler &cgh) {
        auto w_acc = w_buf.get_access<access::mode::read_write>(cgh);
        auto A_acc = A_buf.get_access<access::mode::read>(cgh);
        cgh.single_task<class initKernel2>([=]() {
          w_acc[0] = A_acc[i * n + j];
        });
      });
      pbsize_t i_rounded = (i + 255) / 256 * 256;
      if (i_rounded > 0) {
        q.submit([&](handler &cgh) {
          auto A_acc = A_buf.get_access<access::mode::read>(cgh);
          auto sumr = reduction(w_buf, cgh, plus<>());
          cgh.parallel_for<class reductionKernel2>(nd_range<1>(i_rounded, 256), sumr,
                                                   [=](nd_item<1> item, auto &sumr_arg) {
                                                     idx_t k = item.get_global_id(0);
                                                     if (k < i) {
                                                       sumr_arg += -A_acc[i * n + k] * A_acc[k * n + j];
                                                     }
                                                   });
        });
      }
      q.submit([&](handler &cgh) {
        auto w_acc = w_buf.get_access<access::mode::read>(cgh);
        auto A_acc = A_buf.get_access<access::mode::read_write>(cgh);
        cgh.single_task<class AKernel2>([=]() {
          A_acc[i * n + j] = w_acc[0];
        });
      });
    }
  }

  for (idx_t i = 0; i < n; i++) {
    q.submit([&](handler &cgh) {
      auto w_acc = w_buf.get_access<access::mode::read_write>(cgh);
      auto b_acc = b_buf.get_access<access::mode::read>(cgh);
      cgh.single_task<class initKernel3>([=]() {
        w_acc[0] = b_acc[i];
      });
    });
    pbsize_t i_rounded = (i + 255) / 256 * 256;
    if (i_rounded > 0) {
      q.submit([&](handler &cgh) {
        auto A_acc = A_buf.get_access<access::mode::read>(cgh);
        auto y_acc = y_buf.get_access<access::mode::read>(cgh);
        auto sumr = reduction(w_buf, cgh, plus<>());
        cgh.parallel_for<class reductionKernel3>(nd_range<1>(i_rounded, 256), sumr,
                                                 [=](nd_item<1> item, auto &sumr_arg) {
                                                   idx_t j = item.get_global_id(0);
                                                   if (j < i) {
                                                     sumr_arg += -A_acc[i * n + j] * y_acc[j];
                                                   }
                                                 });
      });
    }
    q.submit([&](handler &cgh) {
      auto y_acc = y_buf.get_access<access::mode::read_write>(cgh);
      auto w_acc = w_buf.get_access<access::mode::read>(cgh);
      cgh.single_task<class yKernel>([=]() {
        y_acc[i] = w_acc[0];
      });
    });
  }
  for (idx_t i = n - 1; i >= 0; i--) {
    q.submit([&](handler &cgh) {
      auto w_acc = w_buf.get_access<access::mode::read_write>(cgh);
      auto y_acc = y_buf.get_access<access::mode::read>(cgh);
      cgh.single_task<class initKernel4>([=]() {
        w_acc[0] = y_acc[i];
      });
    });
    pbsize_t i_rounded = (n - i - 1 + 255) / 256 * 256;
    if (i_rounded > 0) {
      q.submit([&](handler &cgh) {
        auto A_acc = A_buf.get_access<access::mode::read>(cgh);
        auto x_acc = x_buf.get_access<access::mode::read>(cgh);
        auto sumr = reduction(w_buf, cgh, plus<>());
        cgh.parallel_for<class reductionKernel4>(nd_range<1>(i_rounded, 256), sumr,
                                                 [=](nd_item<1> item, auto &sumr_arg) {
                                                   idx_t j = item.get_global_id(0) + i + 1;
                                                   if (j < n) {
                                                     sumr_arg += -A_acc[i * n + j] * x_acc[j];
                                                   }
                                                 });
      });
    }
    q.submit([&](handler &cgh) {
      auto x_acc = x_buf.get_access<access::mode::read_write>(cgh);
      auto w_acc = w_buf.get_access<access::mode::read>(cgh);
      auto A_acc = A_buf.get_access<access::mode::read>(cgh);
      cgh.single_task<class xKernel>([=]() {
        x_acc[i] = w_acc[0] / A_acc[i * n + i];
      });
    });
  }
  q.wait_and_throw();
}

void run(State &state, pbsize_t pbsize) {
  pbsize_t n = pbsize; // 2000



  auto A = state.allocate_array<real>({n, n}, /*fakedata*/ true, /*verify*/ false, "A");
  auto b = state.allocate_array<real>({n}, /*fakedata*/ true, /*verify*/ false, "b");
  auto x = state.allocate_array<real>({n}, /*fakedata*/ false, /*verify*/ true, "x");

  queue q(default_selector{});
  {
    buffer<real, 1> A_buf(A.data(), range<1>(n * n));
    buffer<real, 1> b_buf(b.data(), range<1>(n));
    buffer<real, 1> x_buf(x.data(), range<1>(n));
    buffer<real, 1> y_buf(n);


    for (auto &&_ : state.manual()) {
      ensure_fullrank(n, A);
      {
        auto &&scope = _.scope();
        mykernel(q, n, A_buf, b_buf, x_buf, y_buf);
      }
    }
  }
}