from chainer import function
from chainer import function_set
from chainer.functions import batch_normalization
from chainer.functions import concat
from chainer.functions import convolution_2d
from chainer.functions import pooling_2d
from chainer.functions import relu
from chainer import variable


class InceptionBN(function.Function):
    """Inception module in new GoogLeNet with BN."""

    def __init__(self, in_channels, out1, proj3, out3, proj33, out33,
                 pooltype, proj_pool=None, stride=1):
        if out1 > 0:
            assert stride == 1
            assert proj_pool is not None

        self.f = function_set.FunctionSet(
            proj3=convolution_2d.Convolution2D(
                in_channels, proj3, 1, nobias=True),
            conv3=convolution_2d.Convolution2D(
                proj3, out3, 3, pad=1, stride=stride, nobias=True),
            proj33=convolution_2d.Convolution2D(
                in_channels, proj33, 1, nobias=True),
            conv33a=convolution_2d.Convolution2D(
                proj33, out33, 3, pad=1, nobias=True),
            conv33b=convolution_2d.Convolution2D(
                out33, out33, 3, pad=1, stride=stride, nobias=True),
            proj3n=batch_normalization.BatchNormalization(proj3),
            conv3n=batch_normalization.BatchNormalization(out3),
            proj33n=batch_normalization.BatchNormalization(proj33),
            conv33an=batch_normalization.BatchNormalization(out33),
            conv33bn=batch_normalization.BatchNormalization(out33),
        )

        if out1 > 0:
            self.f.conv1 = convolution_2d.Convolution2D(
                in_channels, out1, 1, stride=stride, nobias=True)
            self.f.conv1n = batch_normalization.BatchNormalization(out1)

        if proj_pool is not None:
            self.f.poolp = convolution_2d.Convolution2D(
                in_channels, proj_pool, 1, nobias=True)
            self.f.poolpn = batch_normalization.BatchNormalization(proj_pool)

        if pooltype == 'max':
            self.f.pool = pooling_2d.MaxPooling2D(3, stride=stride, pad=1)
        elif pooltype == 'avg':
            self.f.pool = pooling_2d.AveragePooling2D(3, stride=stride, pad=1)
        else:
            raise NotImplementedError()

    def forward(self, x):
        f = self.f

        self.x = variable.Variable(x[0])
        outs = []

        if hasattr(f, 'conv1'):
            h1 = f.conv1(self.x)
            h1 = f.conv1n(h1)
            h1 = relu.relu(h1)
            outs.append(h1)

        h3 = relu.relu(f.proj3n(f.proj3(self.x)))
        h3 = relu.relu(f.conv3n(f.conv3(h3)))
        outs.append(h3)

        h33 = relu.relu(f.proj33n(f.proj33(self.x)))
        h33 = relu.relu(f.conv33an(f.conv33a(h33)))
        h33 = relu.relu(f.conv33bn(f.conv33b(h33)))
        outs.append(h33)

        p = f.pool(self.x)
        if hasattr(f, 'poolp'):
            p = relu.relu(f.poolpn(f.poolp(p)))
        outs.append(p)

        self.y = concat.concat(outs, axis=1)
        return self.y.data,

    def backward(self, x, gy):
        self.y.grad = gy[0]
        self.y.backward()
        return self.x.grad,

    def to_gpu(self, device=None):
        super(InceptionBN, self).to_gpu(device)
        self.f.to_gpu(device)

    @property
    def parameters(self):
        return self.f.parameters

    @parameters.setter
    def parameters(self, params):
        self.f.parameters = params

    @property
    def gradients(self):
        return self.f.gradients

    @gradients.setter
    def gradients(self, grads):
        self.f.gradients = grads
