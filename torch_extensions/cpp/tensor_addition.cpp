#include <torch/extension.h>
#include <iostream>
#include <vector>

torch::Tensor add_forward(torch::Tensor A,torch::Tensor B) {return A+B;}

torch::Tensor add_backward(torch::Tensor grad_output) {return grad_output;}


PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
m.def("add_forward", &add_forward, "Add forward");
m.def("add_backward", &add_backward, "Add backward");

}