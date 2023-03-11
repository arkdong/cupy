
import pytest

import cupy
from cupy import testing
from cupyx.scipy.signal._iir_utils import apply_iir

import numpy as np


class TestIIRUtils:
    def _sequential_impl(self, x, b, zi=None):
        t = x.copy()
        y = cupy.empty_like(x, dtype=cupy.float64)

        n = t.size
        k = b.size

        for i in range(n):
            y[i] = t[i]
            upper_bound = i if i < k and zi is None else k
            for j in range(1, upper_bound + 1):
                arr = y
                if i < k and zi is not None:
                    if j > i:
                        arr = zi

                y[i] += b[j - 1] * arr[i - j]
        return y

    def _sequential_impl_nd(self, x, b, axis, zi=None):
        n = x.shape[axis]
        x = cupy.moveaxis(x, axis, -1)
        x_shape = x.shape
        x = x.reshape(-1, n)
        y = cupy.empty_like(x, dtype=cupy.float64)

        for i in range(x.shape[0]):
            y[i] = self._sequential_impl(x[i], b)

        y = y.reshape(x_shape)
        y = cupy.moveaxis(y, -1, axis)
        return y

    @pytest.mark.parametrize('size', [11, 20, 51, 120, 128, 250])
    @pytest.mark.parametrize('order', [1, 2, 3, 4, 5])
    def test_order(self, size, order):
        signs = cupy.tile([1, -1], int(2 * np.ceil(size / 4)))
        x = cupy.arange(3, size + 3, dtype=cupy.float64) * signs[:size]
        b = testing.shaped_random((order,))
        seq = self._sequential_impl(x, b)
        par = apply_iir(x, b)
        testing.assert_allclose(seq, par)

    @pytest.mark.parametrize('size', [11, 20, 51, 120, 128, 250])
    @pytest.mark.parametrize('order', [1, 2, 3, 4, 5])
    def test_order_ndim(self, size, order):
        signs = cupy.tile([1, -1], int(2 * np.ceil(size / 4)))

        x = [cupy.arange(3 + i, size + 3 + i, dtype=cupy.float64) *
             signs[:size] for i in range(3)]
        x = [cupy.expand_dims(e, 0) for e in x]
        x = cupy.concatenate(x, axis=0)

        final_shape = [4, 5]
        final_shape += list(x.shape)

        x = cupy.broadcast_to(x, final_shape)
        x = x.copy()
        b = testing.shaped_random((order,))
        for axis in range(0, len(final_shape)):
            par = apply_iir(x, b, axis)
            seq = self._sequential_impl_nd(x, b, axis)
            testing.assert_allclose(seq, par)

    @pytest.mark.parametrize('size', [11, 20, 51, 120, 128, 250])
    @pytest.mark.parametrize('order', [1, 2, 3, 4, 5])
    def test_order_zero_starting(self, size, order):
        signs = cupy.tile([1, -1], int(2 * np.ceil(size / 4)))
        zi = cupy.zeros(order)
        x = cupy.arange(3, size + 3, dtype=cupy.float64) * signs[:size]
        b = testing.shaped_random((order,))
        seq = self._sequential_impl(x, b, zi=zi)
        par = apply_iir(x, b, zi=zi)
        par2 = apply_iir(x, b)
        testing.assert_allclose(par, par2)
        testing.assert_allclose(seq, par)

    @pytest.mark.parametrize('size', [11, 20, 51, 120, 128, 250])
    @pytest.mark.parametrize('order', [1, 2, 3, 4, 5])
    def test_order_starting_cond(self, size, order):
        signs = cupy.tile([1, -1], int(2 * np.ceil(size / 4)))
        zi = testing.shaped_random((order,))
        x = cupy.arange(3, size + 3, dtype=cupy.float64) * signs[:size]
        b = testing.shaped_random((order,))
        seq = self._sequential_impl(x, b, zi=zi)
        par = apply_iir(x, b, zi=zi)
        testing.assert_allclose(seq, par)
