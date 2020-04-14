from setuptools import setup, Extension
from torch.utils import cpp_extension

setup(name='tensor_addition',
      ext_modules=[cpp_extension.CppExtension('tensor_addition', ['tensor_addition.cpp'])],
      cmdclass={'build_ext': cpp_extension.BuildExtension})