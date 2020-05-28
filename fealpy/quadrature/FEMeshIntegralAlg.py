import numpy as np

class FEMeshIntegralAlg():
    def __init__(self, mesh, q, cellmeasure=None):
        self.mesh = mesh
        self.integrator = mesh.integrator(q, 'cell')
        self.cellmeasure = cellmeasure if cellmeasure is not None \
                else mesh.entity_measure('cell')

        self.edgemeasure = mesh.entity_measure('edge')
        self.edgebarycenter = mesh.entity_barycenter('edge')
        self.edgeintegrator = mesh.integrator(q, 'edge')

        GD = mesh.geom_dimension()
        if GD == 3:
            self.facemeasure = mesh.entity_measure('face')
            self.facebarycenter = mesh.entity_measure('face')
            self.faceintegrator = mesh.integrator(q, 'face') 
        else:
            self.facemeasure = self.edgemeasure
            self.facebarycenter = self.edgebarycenter
            self.faceintegrator = self.edgeintegrator

    def matrix_integral(self, basis0, basis1):
        pass

    def edge_integral(self, u, edgetype=False, q=None, barycenter=False):
        mesh = self.mesh

        qf = self.edgeintegrator if q is None else mesh.integrator(q, 'edge')
        bcs, ws = qf.quadpts, qf.weights

        if barycenter:
            val = u(bcs)
        else:
            ps = mesh.bc_to_point(bcs, etype='edge')
            val = u(ps)

        if edgetype is True:
            e = np.einsum('i, ij..., j->j...', ws, val, self.edgemeasure)
        else:
            e = np.einsum('i, ij..., j->...', ws, val, self.edgemeasure)
        return e

    def face_integral(self, u, facetype=False, q=None, barycenter=False):
        mesh = self.mesh

        qf = self.faceintegrator if q is None else mesh.integrator(q, 'face')
        bcs, ws = qf.quadpts, qf.weights

        if barycenter:
            val = u(bcs)
        else:
            ps = mesh.bc_to_point(bcs, etype='face')
            val = u(ps)

        dim = len(ws.shape)
        s0 = 'abcde'
        s1 = '{}, {}j..., j->j...'.format(s0[0:dim], s0[0:dim])
        if facetype is True:
            e = np.einsum(s1, ws, val, self.facemeasure)
        else:
            e = np.einsum(s1, ws, val, self.facemeasure)
        return e

    def cell_integral(self, u, celltype=False, q=None, barycenter=False):
        mesh = self.mesh

        qf = self.integrator if q is None else mesh.integrator(q, 'cell')
        bcs, ws = qf.quadpts, qf.weights

        if barycenter:
            val = u(bcs)
        else:
            ps = mesh.bc_to_point(bcs, etype='cell')
            val = u(ps)
        dim = len(ws.shape)
        s0 = 'abcde'
        s1 = '{}, {}j..., j->j...'.format(s0[0:dim], s0[0:dim])
        if celltype is True:
            e = np.einsum(s1, ws, val, self.cellmeasure)
        else:
            e = np.einsum(s1, ws, val, self.cellmeasure)
        return e

    def integral(self, u, celltype=False, barycenter=True):
        qf = self.integrator
        bcs = qf.quadpts # 积分点 (NQ, 3)
        ws = qf.weights # 积分点对应的权重 (NQ, )
        if barycenter:
            val = u(bcs)
        else:
            ps = self.mesh.bc_to_point(bcs) # (NQ, NC, 2)
            val = u(ps)
        dim = len(ws.shape)
        s0 = 'abcde'
        s1 = '{}, {}j..., j->j...'.format(s0[0:dim], s0[0:dim])
        e = np.einsum(s1, ws, val, self.cellmeasure)
        if celltype is True:
            return e
        else:
            return e.sum()

    def L2_norm(self, uh, celltype=False):
        def f(x):
            return uh(x)**2
        e = self.integral(f, celltype=celltype)
        if celltype is False:
            return np.sqrt(e.sum())
        else:
            return np.sqrt(e)

    def L2_norm_1(self, uh, celltype=False):
        def f(x):
            return np.sum(uh**2, axis=-1)*self.cellmeasure

        e = self.integral(f, celltype=celltype)
        if celltype is False:
            return np.sqrt(e.sum())
        else:
            return np.sqrt(e)

    def L1_error(self, u, uh, celltype=False):
        def f(x):
            xx = self.mesh.bc_to_point(x)
            return np.abs(u(xx) - uh(x))
        e = self.integral(f, celltype=celltype)
        if celltype is False:
            return e.sum()
        else:
            return e
        return

    def L2_error(self, u, uh, celltype=False):
        def f(bc):
            xx = self.mesh.bc_to_point(bc)
            return (u(xx) - uh(bc))**2
        e = self.integral(f, celltype=celltype)
        if celltype is False:
            return np.sqrt(e.sum())
        else:
            return np.sqrt(e)
        return 

    def L2_error_uI_uh(self, uI, uh, celltype=False):
        def f(x):
            return (uI(x) - uh(x))**2
        e = self.integral(f, celltype=celltype)
        if celltype is False:
            return np.sqrt(e.sum())
        else:
            return np.sqrt(e)
        return 

    def Lp_error(self, u, uh, p, celltype=False):
        def f(x):
            xx = self.mesh.bc_to_point(x)
            return np.abs(u(xx) - uh(x))**p
        e = self.integral(f, celltype=celltype)
        if celltype is False:
            return e.sum()**(1/p)
        else:
            return e**(1/p)
        return 
