import numpy as np
import numpy.linalg as la
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.patches import Ellipse
import time
from copy import deepcopy

# define constraints for the optimizer to use later on
# minimum and maximum ranges of detection
r_min = 10
r_max = 1000

# maximum predicted velocity (90m/s~200mph)
v_max = 90

# maximum own-ship velocity (23m/s~50mph)
vo_max = 23

po=np.array([[0.,0.]]).T
vo=np.array([[0.,20.]]).T

# generate an example trajectory to calculate LOS vectors and TTC
actual_pis=[np.array([[-30.,100.]]).T, np.array([[30., 50.]]).T]
actual_vis=[np.array([[20.,0.]]).T, np.array([[-20., 0.]]).T]

ec=vo/np.linalg.norm(vo)

# def calculate_trajectory_last(at, ls, t_s, ec, tau):
#     if len(ls)<2:
#         raise
#     lt = ls[-1]
#     ls = ls[0:-1]
#     t = t_s[-1]
#     t_s = t_s[0:-1]
#     # get the unit vector perpendicular to the camera normal vector
#     ecp = np.array([[0, -1],[1,0]]) @ ec

#     # solve the min-norm problem
#     A=[]
#     for i in range(len(ls)):
#         Ap = []
#         for j in range(i):
#             Ap.append(np.zeros((2,1)))
#         Ap.append(ls[i])
#         for j in range(i+1,len(ls)+1):
#             Ap.append(np.zeros((2,1)))
#         Ap.append(np.eye(2)*(t-t_s[i]))
#         A1 = np.concatenate(Ap,axis=1)
#         A.append(A1)
#     A2 = []
#     for i in range(len(ls)):
#         A2.append(np.zeros((2,1)))
#     A2.append(ecp)
#     A2.append(np.eye(2)*(t-tau))
#     A2 = np.concatenate(A2, axis=1)
#     A.append(A2)
#     A = np.concatenate(A,axis=0)

#     b = []
#     for i in range(len(ls)):
#         b.append(at*lt+vo*(t-t_s[i]))
#     b.append(at*lt+vo*(t-tau))
#     b = np.concatenate(b,axis=0)

#     x = np.linalg.pinv(A)@b

#     # set the result up as a possible trajectory to plot along 
#     # with the original example
#     pit = at*lt
#     vi = x[-2:]
#     return pit, vi


class Trajectories:
    def __init__(self, num_intruders, num_particles, initial_pos, velocities, ts) -> None:
        self.poss = deepcopy(initial_pos)
        self.vels = deepcopy(velocities)
        self.num_intruders = num_intruders
        self.num_particles = num_particles
        self.ts = ts

    def update(self):
        for i in range(len(self.poss)):
            self.poss[i] += self.vels[i]*self.ts
    
    def get_own_position(self):
        return self.poss[0]
    
    def get_intruder_positions(self):
        return self.poss[1:self.num_intruders+1]
    
    def get_particle_positions(self):
        particleps = []
        for i in range(self.num_intruders):
            particleps.append(self.poss[self.num_intruders+1+i*self.num_particles:self.num_intruders+1+(i+1)*self.num_particles])
        return particleps

    def set_particle_positions(self, pposes):
        for i in range(self.num_intruders):
            self.poss[self.num_intruders+1+i*self.num_particles:self.num_intruders+1+(i+1)*self.num_particles] = pposes[i]

class Plotter:
    def __init__(self, num_intruders, num_particles, limits) -> None:
        plt.ion()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot()
        self.num_intruders = num_intruders
        self.num_particles = num_particles
        self.limits = limits
        # list of the x and y coordinates of the ownship
        self.pox = []
        self.poy = []
        # list of list of x and y coordinates of each of the intruders
        self.pix = []
        self.piy = []
        self.particles_x = []
        self.particles_y = []
        for i in range(num_intruders):
            self.pix.append([])
            self.piy.append([])
            self.particles_x.append([])
            self.particles_y.append([])

    def update_plot(self, own_pos, intruder_poses, particle_poses):
        plt.ion()
        head_width = 10
        self.ax.clear()
        # add the points to the respective lists
        self.pox.append(own_pos.item(0))
        self.poy.append(own_pos.item(1))
        for i in range(self.num_intruders):
            # add each intruder position to the list
            self.pix[i].append(intruder_poses[i].item(0))
            self.piy[i].append(intruder_poses[i].item(1))

            # add the particle positions to the lists
            for j in range(self.num_particles):
                self.particles_x[i].append(particle_poses[i][j].item(0))
                self.particles_y[i].append(particle_poses[i][j].item(1))
            # plot the particles of each intruder
            self.ax.plot(self.particles_x[i], self.particles_y[i], marker='.', ls='', markersize=1, zorder=-30, label=f"In. {i+1} Particles")

        # plot each of the actual intruders
        for i in range(self.num_intruders):
            lines=self.ax.plot(self.pix[i],self.piy[i],label=f"Intruder {i+1}")
            if len(self.pix[i]) >= 2:
                self.ax.arrow(self.pix[i][0], self.piy[i][0], self.pix[i][1]-self.pix[i][0], self.piy[i][1]-self.piy[i][0], head_width=head_width, color=lines[0].get_color())
            

        # plot the own-ship path
        self.ax.plot(self.pox,self.poy,label='Own',c='r')
        if len(self.pox)>=2:
            self.ax.arrow(self.pox[0], self.poy[0], self.pox[1]-self.pox[0], self.poy[1]-self.poy[0], color='r', head_width=head_width)

        self.ax.set_title("Positions of Own-ship and Intruders")
        self.ax.set_xlabel("x (m)")
        self.ax.set_ylabel("y (m)")
        self.ax.legend()
        # self.ax.set_xlim(self.limits[0])
        # self.ax.set_ylim(self.limits[1])

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

    def plot_interactive(self):
        plt.ioff()
        fig, ax = plt.subplots()

        initial_i = 0
        particle_plots = []
        intruder_plots = []
        for i in range(self.num_intruders):
            l,=plt.plot(self.particles_x[i][0:self.num_particles], self.particles_x[i][0:self.num_particles],marker='.', ls='', markersize=1, label=f'Particles Intruder {i+1}')
            particle_plots.append(l)
        for i in range(self.num_intruders):
            li, = plt.plot(self.pix[i][0], self.piy[i][0], marker='.', ls='', markersize=10, label=f'Intruder {i+1}')
            intruder_plots.append(li)
        l0, = plt.plot(self.pox[0], self.poy[0], c='r', marker='.', ls='', markersize=10, label='Ownship')
        xlims = self.ax.get_xlim()
        ylims = self.ax.get_ylim()
        ax = plt.axis([xlims[0], xlims[1], ylims[0], ylims[1]])
        plt.legend()

        axamp = plt.axes([0.25, .03, 0.50, 0.02])
        # Slider
        samp = Slider(axamp, 'Timestep', 0, len(self.pox)-1, valinit=initial_i, valstep=1)

        def update(val):
            # amp is the current value of the slider
            j = samp.val
            # update curve
            for i in range(self.num_intruders):
                particle_plots[i].set_xdata(self.particles_x[i][self.num_particles*j:self.num_particles*(j+1)])
                particle_plots[i].set_ydata(self.particles_y[i][self.num_particles*j:self.num_particles*(j+1)])
                intruder_plots[i].set_xdata(self.pix[i][j])
                intruder_plots[i].set_ydata(self.piy[i][j])
            l0.set_xdata(self.pox[j])
            l0.set_ydata(self.poy[j])
            # redraw canvas while idle
            fig.canvas.draw_idle()

        # call update function on slider value change
        samp.on_changed(update)

        plt.show()

class Particle_Filter:
    def __init__(self, num_particles, l1, l2, tau, po0, po1, ec, r_min, r_max, v_max, ts) -> None:
        self.t = ts
        self.num_particles = num_particles
        self.po0 = po0
        self.pos = [po0, po1]
        self.ts = ts
        self.Rinv = np.diag([1/0.05**2, 1/0.05**2])
        tau += ts
        self.taus = [tau]
        self.ec = ec
        self.lms = deepcopy([l1,l2])
        lms_norm = [l1/l1.item(1), l2/l2.item(1)]
        self.weights = []
        self.pi0s = []
        self.particle_p = []
        self.vis = []
        self.r_min = r_min
        while len(self.pi0s) < num_particles:
            # randomly noisify the measurements
            lus = []
            for lm_norm in lms_norm:
                l_u = lm_norm
                l_u[0,0] += np.random.normal(0,0.001)
                l_u /= np.linalg.norm(l_u)
                lus.append(l_u)

            tau_u = tau + np.random.normal(0, 0.5)

            a1_u = (r_max-r_min)*np.random.random()+ r_min
            pos, vel = self.calculate_trajectory_first(a1_u, lus, ec, tau_u, self.pos)
            if np.linalg.norm(vel)<=v_max:
                self.pi0s.append(pos)
                self.particle_p.append(pos+vel*ts)
                self.vis.append(vel)
                self.weights.append(1)
    def get_particle_positions(self):
        return self.particle_p

    def get_future_positions(self, delta_t):
        future_pos = []
        for i in range(self.num_particles):
            future_pos.append(self.particle_p[i] + self.vis[i]*delta_t)
        return future_pos
    
    # Implementation of Gauss-Newton batch discrete-time estimation (taken from State Estimation for Robotics by Tim Barfoot, pp 128-134)
    def calculate_velocity_improved(self, ls, pk, vk, pOs):
        def calc_G(x, po):
            pr = x[0:2] - po
            prx = pr.item(0)
            pry = pr.item(1)
            denom = pow(prx**2+pry**2, 3/2)
            G = np.array([[pry**2, -prx*pry, 0, 0],
                          [-prx*pry, prx**2, 0, 0]])/denom
            return G
        def g(x, po):
            pr = x[0:2] - po
            return pr/la.norm(pr)
        F = np.eye(4)
        F[0:2,2:] = -np.eye(2)*self.ts # we're working the trajectory back from the current position

        P0 = [0.001, 0.001, 1., 1.]
        Q = [0.01]*4
        R = [0.05**2]*2

        x = [deepcopy(pk), deepcopy(vk)]
        x0 = deepcopy(x)
        x0 = np.concatenate(x0, axis=0)
        pn = deepcopy(pk)
        k = len(ls)
        while len(x) < 2*k:
            pn -= vk*self.ts
            x.append(deepcopy(pn))
            x.append(vk)
        x = np.concatenate(x, axis=0)
        dx = np.ones_like(x)

        W = np.diag(P0 + Q*(k-1)+R*k)
        Winv = la.inv(W)
        iter = 0
        while (dx.max() > 0.01 or dx.min() < -0.01) and iter < 10:
            e = np.zeros((6*k, 1))
            H = np.zeros((6*k,4*k))
            H[:4*k,:4*k] = np.eye(4*k)
            for i in range(k-1):
                H[4*(i+1):4*(i+2), 4*i:4*(i+1)]=F
            offset = 4*k
            for i in range(k):
                H[offset+2*i:offset+2*(i+1),4*i:4*(i+1)] = calc_G(x[4*i:4*(i+1)], pOs[-i-1])
                if i == 0:
                    e[0:4] = x0 - x[0:4]
                else:
                    e[4*i:4*(i+1)] = F @ x[4*(i-1):4*i] - x[4*i:4*(i+1)]
                e[offset+2*i:offset+2*(i+1)] = ls[-i-1] - g(x[4*i:4*(i+1)], pOs[-i-1])
            dx = la.pinv(H.T @ Winv @ H) @ H.T @ Winv @ e
            x += dx
            iter += 1
        return x[0:2], x[2:4], x[4*(k-1):4*(k-1)+2] # return pk, vk, p0



    
    def calculate_trajectory_first(self, a1, ls, ec, tau, pos):
        if len(ls)<2:
            raise
        l1 = ls[0]
        ls = ls[1:]
        po0 = pos[0]
        pos = pos[1:]
        # get the unit vector perpendicular to the camera normal vector
        ecp = np.array([[0, -1],[1,0]]) @ ec

        # solve the min-norm problem
        A=[]
        for i in range(len(ls)):
            Ap = []
            for j in range(i):
                Ap.append(np.zeros((2,1)))
            Ap.append(ls[i])
            for j in range(i+1,len(ls)+1):
                Ap.append(np.zeros((2,1)))
            Ap.append(-np.eye(2)*ts*(i+1))
            A1 = np.concatenate(Ap,axis=1)
            A.append(A1)
        A2 = []
        for i in range(len(ls)):
            A2.append(np.zeros((2,1)))
        A2.append(ecp)
        A2.append(-np.eye(2)*tau)
        A2 = np.concatenate(A2, axis=1)
        A.append(A2)
        A = np.concatenate(A,axis=0)

        b = []
        for i in range(len(ls)):
            b.append(po0-pos[i]+a1*l1)
        b.append(-vo*tau+a1*l1)
        b = np.concatenate(b,axis=0)

        x = np.linalg.pinv(A)@b

        # set the result up as a possible trajectory to plot along 
        # with the original example
        pi0 = a1*l1
        vi = x[-2:]
        return pi0, vi
    
    def update(self, lm, po, tau):
        # update the weights
        self.pos.append(po)
        for i in range(self.num_particles):
            # propogate the dynamics
            self.particle_p[i] += self.vis[i]*self.ts

            # get the weights based on the measurement
            phat = self.particle_p[i]-po
            phat /= np.linalg.norm(phat)
            self.weights[i] = np.exp(-1/2. * (lm-phat).T @ self.Rinv @ (lm-phat)).item(0)
        sum = np.sum(self.weights)
        self.weights = [x/sum for x in self.weights]
        self.lms.append(lm)
        self.t += self.ts
        self.taus.append(tau + self.t)

        # resample
        old_pi0s = deepcopy(self.pi0s)

        rr = np.random.rand()/self.num_particles
        i = 0
        cc = self.weights[i]
        for mm in range(self.num_particles):
            u = rr + (mm-1)/self.num_particles
            while u > cc:
                i += 1
                cc += self.weights[i]
            l = old_pi0s[i] - self.po0
            a0 = max(np.linalg.norm(l) + np.random.normal(0, 5), self.r_min)
            l /= l.item(1)
            l[0,0] += np.random.normal(0,0.001)
            l /= np.linalg.norm(l)
            pi0, vi = self.calculate_trajectory_first(a0, [l]+self.lms[1:],self.ec, np.average(self.taus), self.pos) # use this to get an initial guess of the position and velocity
            pk, vk, pi0n = self.calculate_velocity_improved(self.lms, pi0+vi*self.t, vi, self.pos)
            self.particle_p[mm] = pk
            self.vis[mm] = vk
            self.pi0s[mm]=pi0n

def plot_futures(t, ts, filters, actual_pis, actual_vis, po, vo, xlims, ylims):
    plt.ioff()
    fig, ax = plt.subplots()

    initial_dt = 0
    max_dt = 5.
    problematic_particle_plots = []
    not_problematic_particle_plots = []
    intruder_plots = []
    p_ellipses = []
    ax = plt.gca()
    for i in range(len(filters)):
        pos = filters[i].get_future_positions(initial_dt)
        problematic = []
        not_problematic = []
        for p in pos:
            if la.norm(p-po-vo*t)/(initial_dt+0.0001)<=vo_max:
                problematic.append(p)
            else:
                not_problematic.append(p)
        
        l,=plt.plot([p.item(0) for p in problematic], [p.item(1) for p in problematic],marker='.', ls='', markersize=1, label=f'P Particles Intruder {i+1}')
        nl,=plt.plot([p.item(0) for p in not_problematic], [p.item(1) for p in not_problematic],marker='.', ls='', markersize=1, label=f'Not P Particles Intruder {i+1}')
        if len(problematic) > 1:
            centroid, a, b, alpha = get_ellipse_for_printing(problematic)
        else:
            centroid, a, b, alpha = (0,0),5.,5.,0.
        ellipse = Ellipse(centroid, a, b, alpha, edgecolor='k', fc='None',lw=2)
        ax.add_artist(ellipse)
        p_ellipses.append(ellipse)
        problematic_particle_plots.append(l)
        not_problematic_particle_plots.append(nl)
    for i in range(len(actual_pis)):
        p = actual_pis[i]+actual_vis[i]*(t+initial_dt)
        li, = plt.plot(p.item(0), p.item(1), marker='.', ls='', markersize=10, label=f'Intruder {i+1}')
        intruder_plots.append(li)
    p = po+vo*(t+initial_dt)
    l0, = plt.plot(p.item(0), p.item(1), c='r', marker='.', ls='', markersize=10, label='Ownship')
    ax = plt.axis([xlims[0], xlims[1], ylims[0], ylims[1]])
    plt.legend()
    plt.title(f"Future Predictions for t={t:.3f}s")

    axamp = plt.axes([0.25, .03, 0.50, 0.02])
    # Slider
    samp = Slider(axamp, 'Time', t, t+max_dt, valinit=initial_dt, valstep=ts)

    def update(val):
        # amp is the current value of the slider
        tf = samp.val
        # update curve
        for i in range(len(filters)):
            pos = filters[i].get_future_positions(tf-t)
            problematic = []
            not_problematic = []
            for p in pos:
                if la.norm(p-po-vo*t)/(tf-t+0.0001)<=vo_max:
                    problematic.append(p)
                else:
                    not_problematic.append(p)
            problematic_particle_plots[i].set_xdata([p.item(0) for p in problematic])
            problematic_particle_plots[i].set_ydata([p.item(1) for p in problematic])
            not_problematic_particle_plots[i].set_xdata([p.item(0) for p in not_problematic])
            not_problematic_particle_plots[i].set_ydata([p.item(1) for p in not_problematic])
            if len(problematic) > 1:
                centroid, a, b, alpha = get_ellipse_for_printing(problematic)
            else:
                 centroid, a, b, alpha = (0,0),5.,5.,0.
            p_ellipses[i].set_center(centroid)
            p_ellipses[i].set_width(a)
            p_ellipses[i].set_height(b)
            p_ellipses[i].set_angle(alpha)
            p = actual_pis[i]+actual_vis[i]*(tf)
            intruder_plots[i].set_xdata(p.item(0))
            intruder_plots[i].set_ydata(p.item(1))
        p = po+vo*(tf)
        l0.set_xdata(p.item(0))
        l0.set_ydata(p.item(1))
        # redraw canvas while idle
        fig.canvas.draw()

    # call update function on slider value change
    samp.on_changed(update)

    plt.show()
    plt.ion()

def get_ellipse_for_printing(points):
    center = np.mean(np.asarray(points), axis=0)
    reshaped = np.reshape(np.stack(points, axis=1),(2,-1))
    A = np.cov(reshaped)#np.zeros((center.shape[0],center.shape[0]))
    # n = len(points)
    # for point in points:
    #     A += (point - center) @ (point - center).T/(n-1)
    
    # print A

    # V is the rotation matrix that gives the orientation of the ellipsoid.
    # https://en.wikipedia.org/wiki/Rotation_matrix
    # http://mathworld.wolfram.com/RotationMatrix.html
    U, D, V = la.svd(A)
    
    # x, y radii.
    l1, l2 = np.sqrt(D)
    # Major and minor semi-axis of the ellipse.
    s = np.sqrt(5.991) # cooresponds to 95% confidence interval
    dx, dy = 2 * l1 * s, 2 * l2 * s
    a, b = max(dx, dy), min(dx, dy)
    # Eccentricity
    e = np.sqrt(a ** 2 - b ** 2) / a

    # print '\n', U
    # print D
    # print V, '\n'
    # Orientation angle (with respect to the x axis counterclockwise).
    alpha = np.rad2deg(np.arctan2(V[0][1],V[0][0]))
    centroid = (center.item(0), center.item(1))
    return centroid, a, b, alpha

num_particles = 1000
particle_p = deepcopy([po]+actual_pis)
particle_v = [vo]+actual_vis

t=0.
ts = 0.2
tstop = 5.
steps = 0
num_intruders = len(actual_pis)
lm_col = []
filters = []
for i in range(num_intruders):
    lm_col.append([])

traj = Trajectories(num_intruders, num_particles, particle_p, particle_v, ts)
plotter = Plotter(num_intruders, num_particles, [[-130,70],[-5,130]])
while t < tstop:
    for i in range(num_intruders):
        lm = traj.get_intruder_positions()[i] - traj.get_own_position()
        # corrupt the bearing measurement with noise
        lm /= lm.item(1)
        lm[0,0] += np.random.normal(0,0.0005)
        lm /= np.linalg.norm(lm)
        lm_col[i].append(lm)
        # calculate tau
        tau = ((traj.get_own_position()-traj.get_intruder_positions()[i]).T @ ec)/((actual_vis[i]-vo).T @ ec)
        if steps == 1:
            # initialize the filters
            filters.append(Particle_Filter(num_particles, lm_col[i][0], lm_col[i][1], tau, po, po+vo*ts, ec, r_min, r_max, v_max, ts))
        if steps >= 2:
            # weight the particles based on the new bearing measurement
            filters[i].update(lm, traj.get_own_position(), tau)
    if steps >= 1:
        plotter.update_plot(traj.get_own_position(), traj.get_intruder_positions(), [filter.get_particle_positions() for filter in filters])
        plot_futures(t, ts, filters, actual_pis, actual_vis, po, vo, [-200, 200], [0, 200])
    traj.update()
    t+=ts
    steps += 1
    # time.sleep(ts)

plotter.update_plot(traj.get_own_position(), traj.get_intruder_positions(), [filter.get_particle_positions() for filter in filters])
plotter.plot_interactive()
plt.show()