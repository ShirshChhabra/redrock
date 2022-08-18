import os
import unittest
import numpy as np
import cupy as cp
cp_available = False

from .. import rebin

class TestRebin(unittest.TestCase):

    def setUp(self):
        #- Supposed to turn off numba.jit of _trapz_rebin, but coverage
        #- still doesn't see the function.  Leaving this here anyway.
        os.environ['NUMBA_DISABLE_JIT'] = '1'
        try:
            d = cp.cuda.Device()
            cp_available = True
        except Exception:
            cp_available = False

    def tearDown(self):
        del os.environ['NUMBA_DISABLE_JIT']

    def test_centers2edges(self):
        c2e = rebin.centers2edges  #- shorthand
        self.assertTrue(np.allclose(c2e([1,2,3]), [0.5, 1.5, 2.5, 3.5]))
        self.assertTrue(np.allclose(c2e([1,3,5]), [0, 2, 4, 6]))
        self.assertTrue(np.allclose(c2e([1,3,4]), [0, 2, 3.5, 4.5]))

    def test_trapzrebin(self):
        '''Test constant flux density at various binnings'''
        nx = 10
        x = np.arange(nx)*1.1
        y = np.ones(nx)

        #- test various binnings
        for nedge in range(3,10):
            edges = np.linspace(min(x), max(x), nedge)
            yy = rebin.trapz_rebin(x, y, edges=edges)
            self.assertTrue(np.all(yy == 1.0), msg=str(yy))

        #- edges starting/stopping in the interior
        summ = rebin.trapz_rebin(x, y, edges=[0.5, 8.3])[0]
        for nedge in range(3, 3*nx):
            edges = np.linspace(0.5, 8.3, nedge)
            yy = rebin.trapz_rebin(x, y, edges=edges)
            self.assertTrue(np.allclose(yy, 1.0), msg=str(yy))

    def test_centers(self):
        '''Test with centers instead of edges'''
        nx = 10
        x = np.arange(nx)
        y = np.ones(nx)
        xx = np.linspace(0.5, nx-1.5)
        yy = rebin.trapz_rebin(x, y, xx)
        self.assertTrue(np.allclose(yy, 1.0), msg=str(yy))

    def test_error(self):
        '''Test that using edges outside of x range raises ValueError'''
        nx = 10
        x = np.arange(nx)
        y = np.ones(nx)
        with self.assertRaises(ValueError):
            yy = rebin.trapz_rebin(x, y, edges=np.arange(-1, nx-1))
        with self.assertRaises(ValueError):
            yy = rebin.trapz_rebin(x, y, edges=np.arange(1, nx+1))

    def test_nonuniform(self):
        '''test rebinning a non-uniform density'''
        for nx in range(5,12):
            x = np.linspace(0, 2*np.pi, nx)
            y = np.sin(x)
            edges = [0, 2*np.pi]
            yy = rebin.trapz_rebin(x, y, edges=edges)
            self.assertTrue(np.allclose(yy, 0.0))

        x = np.linspace(0, 2*np.pi, 100)
        y = np.sin(x)
        edges = [0, 0.5*np.pi, np.pi, 1.5*np.pi, 2*np.pi]
        yy = rebin.trapz_rebin(x, y, edges=edges)
        self.assertTrue(np.allclose(yy[0:2], 2/np.pi, atol=5e-4))
        self.assertTrue(np.allclose(yy[2:4], -2/np.pi, atol=5e-4))

    def test_gpu_trpazrebin(self):
        '''Test that GPU version matches CPU for constant flux density at various binnings'''
        if (not cp_available):
            self.assertTrue(True)
            return
        nx = 10
        x = np.arange(nx)*1.1
        y = np.ones(nx)

        #- test various binnings
        for nedge in range(3,10):
            edges = np.linspace(min(x), max(x), nedge)
            yy = rebin.trapz_rebin_batch_gpu(x, y, edges=edges)
            self.assertTrue(np.all(yy == 1.0), msg=str(yy))

        #- edges starting/stopping in the interior
        summ = rebin.trapz_rebin_batch_gpu(x, y, edges=[0.5, 8.3])[0]
        for nedge in range(3, 3*nx):
            edges = np.linspace(0.5, 8.3, nedge)
            yy = rebin.trapz_rebin_batch_gpu(x, y, edges=edges)
            self.assertTrue(np.allclose(yy, 1.0), msg=str(yy))

    def test_gpu_trapzrebin_uneven(self):
        '''test rebinning unevenly spaced x for GPU vs CPU'''
        if (not cp_available):
            self.assertTrue(True)
            return
        x = np.linspace(0, 10, 100)**2
        y = np.sqrt(x)
        edges = np.linspace(0,100,21)
        c = rebin.trapz_rebin(x, y, edges=edges)
        g = rebin.trapz_rebin_batch_gpu(x, y, edges=edges)
        self.assertTrue(np.allclose(c,g))


def test_suite():
    """Allows testing of only this module with the command::

        python setup.py test -m <modulename>
    """
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
