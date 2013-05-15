"""
Riemann Surfaces
"""
import numpy
import scipy
import scipy.linalg as la
import scipy.integrate
import sympy


from abelfunctions.monodromy import monodromy, show_paths
from abelfunctions.homology import homology
from abelfunctions.riemannsurface_path import (
    path_around_branch_point,
    RiemannSurfacePath,
    )
from abelfunctions.riemannsurface_point import RiemannSurfacePoint
from abelfunctions.singularities import genus
from abelfunctions.differentials import differentials
from abelfunctions.utilities import cached_function


import pdb
        

class RiemannSurface(object):
    """
    Class for defining a Riemann surface corresponding to a plane
    algebraic curve.
    """
    def __init__(self, f, x, y):
        self.f = f
        self.x = x
        self.y = y

    def __repr__(self):
        return "Riemann surface defined by the algebraic curve %s." %(self.f)

    def __call__(self, x, y):
        return RiemannSurfacePoint(self, x, y)


    def point(self, x0, y0):
        """
        Returns the point on the Riemann surface closest to
        `(x0,y0)`. (In the event that floating point precision is used
        to calculate the coordinates `(x0,y0)`.
        """
        return RiemannSurfacePoint(self,x0,y0)
 
    def monodromy(self):
        """
        """
        return monodromy(self.f, self.x, self.y)


    def monodromy_graph(self):
        """
        """
        return self.monodromy()[4]


    def base_point(self):
        return self.monodromy()[0]


    def base_sheets(self):
        return self.monodromy()[1]


    def base_lift(self):
        return self.base_sheets()


    def branch_points(self):
        return self.monodromy()[2]


    def monodromy_group(self):
        return self.monodromy()[3]


    def homology(self):
        return homology(self.f, self.x, self.y)


    def holomorphic_differentials(self):
        """ 
        Returns the basis of holomorphic differentials defined on the
        Riemann surface.
        """
        return differentials(self.f, self.x, self.y)

    def differentials(self):
        """
        Alias for RiemannSurface.holomorphic_differentials().
        """
        return self.holomorphic_differentials()


    def genus(self):
        """
        Return the genus of the Riemann surface.
        """
        return genus(self.f, self.x, self.y)


    def cycles(self):
        """
        """
        return self.homology()
    

    @cached_function
    def cycle_paths(self):
        """
        Returns a path in the complex x-plane of the x-points in the
        monodromy path.
        
        Input:

        - i: the index of the c-cycle
        
        Output:

        - a RiemannSurfacePath parameterizing the c-cycle
        """
        abs = numpy.abs

        # get the cycle data from homology: each c-cycle is a list of
        # alternating sheet numbers s_k and branch point / number of
        # rotations tuples (b_{i_k}, n_k)
        a_cycles, b_cycles = self.homology()
        cycles = a_cycles + b_cycles
        
        G = self.monodromy_graph()
        root = G.node[0]['root']
        
        cycle_paths = []
        for cycle in cycles:
            path_segments = []

            # For each (branch point, rotation number) pair appearing in
            # the cycle compute the path segments the complex x-plane
            # going around the given branch points a number of times equal
            # to the rotation number. Add these segments to the list of
            # path segemnts.
            for (bpt, rot) in cycle[1::2]:
                bpt_index = [key for key,data in G.nodes(data=True)
                             if abs(data['value']-bpt) < 1e-15][0]
                bpt_path_segments = path_around_branch_point(G, bpt_index, rot)
                path_segments.extend(bpt_path_segments)

            # Construct the RiemannSurfacePath and append to path list
            x0 = self.base_point()
            y0 = self.base_lift()
            gamma = RiemannSurfacePath(self, (x0,y0),
                                       path_segments=path_segments)

            cycle_paths.append(gamma)

        return cycle_paths


    def integrate(self, omega, x, y, path):
        """
        Integrates the differential `omega`, defined on the
        Riemann surface, on the RiemannSurfacePath `path`.
        
        Input:

        - `omega,x,y`: a Sympy funciton in the variables `x` and `y`

        - `path`: a RiemannSurfacePath defined on the Riemann surface
        """
        x0,y0 = path(0)
        omega = sympy.lambdify((x,y), omega, 'numpy')
        
        # Numerically integrate over each path segment. This is most
        # probably a good idea since it allows for good checkpointing.
        def integrand(t,omega,path):
            (xi,yi),dxdt = path(t, dxdt=True)
            return omega(xi,yi[0]) * dxdt # follow the base fibre

        val = numpy.complex(0)
        val_real = numpy.double(0)
        val_imag = numpy.double(0)
        n = numpy.int(path._num_path_segments)
        for k in xrange(n):
            k = numpy.double(k)

            tpts = numpy.linspace(k/n,(k+1)/n,128)
            fpts = [integrand(tpt,omega,path) for tpt in tpts]
            val += scipy.integrate.trapz(tpts,fpts)

        return val


    def period_matrix(self):
        """
        Returns the period matrix `\tau = (A \; B)` where `A_{ij}` is
        the integral of the `j`th holomorphic differential basis element
        about the cycle `a_i`. (`B` is defined in the same way about the 
        `b`-cycles.)

        Note: this function computes the integrals of the
        differentials over each of the c-cycles and then uses the
        homology data to determine which linear combination of
        c-cycles integrals gives the a- and b-cycles integrals.
        """
        cycles = self.cycle_paths()
        
        differentials = self.holomorphic_differentials()
        g = self.genus()
        x = self.x
        y = self.y

        A = []
        B = []
        for i in xrange(g):
            omega = differentials[i]
            Ai = []
            Bi = []
            for j in xrange(g):
                integral = self.integrate(omega,x,y,cycles[j]) 
                Ai.append(integral)
                
                integral = self.integrate(omega,x,y,cycles[j+g])
                Bi.append(integral)
                
            A.append(Ai)
            B.append(Bi)

        # need to transpose...?
        A = numpy.matrix(A,dtype=numpy.complex)
        B = numpy.matrix(B,dtype=numpy.complex)
        return (A,B)


    def show_paths(self):
        """
        """
        G = self.monodromy_graph()
        show_paths(G)



if __name__ == '__main__':
    from sympy.abc import x,y

    f0 = y**3 - 2*x**3*y - x**8  # Klein curve

    f1 = (x**2 - x + 1)*y**2 - 2*x**2*y + x**4
    f2 = -x**7 + 2*x**3*y + y**3
    f3 = (y**2-x**2)*(x-1)*(2*x-3) - 4*(x**2+y**2-2*x)**2
    f4 = y**2 + x**3 - x**2
    f5 = (x**2 + y**2)**3 + 3*x**2*y - y**3
    f6 = y**4 - y**2*x + x**2   # case with only one finite disc pt
    f7 = y**3 - (x**3 + y)**2 + 1
    f8 = (x**6)*y**3 + 2*x**3*y - 1
    f9 = 2*x**7*y + 2*x**7 + y**3 + 3*y**2 + 3*y
    f10= (x**3)*y**4 + 4*x**2*y**2 + 2*x**3*y - 1  # genus 3

    f11= y**2 - (x-2)*(x-1)*(x+1)*(x+2)  # simple genus one hyperelliptic
    f12 = x**4 + y**4 - 1


    f = f12
    X = RiemannSurface(f,x,y)


    print "\n\tRS"
    print X

    print "\n\tRS: monodromy"
    base_point, base_sheets, branch_points, mon, G = X.monodromy()
    print "\nbase_point:"
    print base_point
    print "\nbase_sheets:"
    for s in base_sheets: print s
    print "\nbranch points:"
    for b in branch_points: print b
    print "\nmonodromy group:"
    for m in mon: print m

    print "\n\tRS: homology"
    a_cycles, b_cycles = X.homology()
    for a in a_cycles:
        print a
    print
    for b in b_cycles:
        print b

    print "\n\tRS: computing cycles"
    cycles = X.cycles()


    print "\n\tRS: computing paths"
    paths = X.cycle_paths()

    print "\n\tRS: plotting a path"
    paths[0].plot3d()

#     print "\n\tRS: period matrix"
#     A,B = X.period_matrix()
#     Omega = numpy.dot(la.inv(A),B)
#     print "\n\tA = "
#     print A
#     print "\n\tB = "
#     print B
#     print "\n\tOmega (abelfunctions)"
#     print Omega
#     print

#     # f11 matrix:
#     M_A = numpy.matrix([[1.078257j]],dtype=numpy.complex)
#     M_B = numpy.matrix([[-1.685750+1.078257j]], dtype=numpy.complex)
    
# #     # f2 matrix:
# #     A = numpy.matrix([[-1.8495720-0.60096222j,1.1430983+1.573339933j],
# #                       [-.71617632+.98573195j, -1.1587974-.37651605j]],
# #                      dtype=numpy.complex)
# #     B = numpy.matrix([[-1.412947298+0.0j,-2.556045689+1.573339862j],
# #                       [-3.749947262+0.0j,-2.591149960-.3765160905j]],
# #                      dtype=numpy.complex)

#     M_Omega = numpy.dot(la.inv(M_A),M_B)    
#     print "\tOmega (maple)\n"
#     print M_Omega


