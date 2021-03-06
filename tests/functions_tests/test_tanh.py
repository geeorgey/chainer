import unittest

import numpy

import chainer
from chainer import cuda
from chainer import functions
from chainer import gradient_check
from chainer.testing import attr


if cuda.available:
    cuda.init()


class TestSigmoid(unittest.TestCase):

    def setUp(self):
        self.x = numpy.random.uniform(-.5, .5, (3, 2)).astype(numpy.float32)
        self.gy = numpy.random.uniform(-.1, .1, (3, 2)).astype(numpy.float32)

    @attr.cudnn
    def test_forward_gpu(self, use_cudnn=True):
        x = chainer.Variable(cuda.to_gpu(self.x))
        y = functions.tanh(x, use_cudnn=use_cudnn)
        y_expect = functions.tanh(chainer.Variable(self.x))
        gradient_check.assert_allclose(y_expect.data, y.data)

    @attr.gpu
    def test_forward_gpu_no_cudnn(self):
        self.test_forward_gpu(False)

    def check_backward(self, x_data, gy_data, use_cudnn=True):
        x = chainer.Variable(x_data)
        y = functions.tanh(x, use_cudnn=use_cudnn)
        y.grad = gy_data
        y.backward()

        func = y.creator
        f = lambda: func.forward((x.data,))
        gx, = gradient_check.numerical_grad(f, (x.data,), (y.grad,))
        gradient_check.assert_allclose(gx, x.grad)

    def test_backward_cpu(self):
        self.check_backward(self.x, self.gy)

    @attr.cudnn
    def test_backward_gpu(self):
        self.check_backward(cuda.to_gpu(self.x), cuda.to_gpu(self.gy))

    @attr.gpu
    def test_backward_gpu_no_cudnn(self):
        self.check_backward(cuda.to_gpu(self.x), cuda.to_gpu(self.gy), False)
