# started over to avoid the use of global variables

import numpy as np
import math
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from itertools import combinations

# define constants 
FRAMES = 250
STARTSIZE = 10
NUMBER = 100
DIMENSION = 2  # dimension of volume, gas and simulation
DT = 0.04       # size of time step in simulation

class Atom:
    def __init__(self, mass, radius, position, velocity):
        self.mass = mass
        self.radius = radius
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        # toevoegen van eigenschap circle maakt het mogelijk om atomen tussen volumes uit te wisselen
        self.circle = plt.Circle(self.position[0:2], self.radius, color='b')

    def move(self):
        self.position += self.velocity * DT
        self.circle.set_center(self.position)
        if DIMENSION > 2: # Kleur bepalen voor hoogte in drie-dimensionale geval
            self.circle.set_color(plt.get_cmap('Blues')(self.position[2] / STARTSIZE))

    def check_atom_collision(self, other: "Atom"):
        ''' functie die bepaalt of er een botsing plaatsheeft tussen self en other. Zo ja, dan worden de snelheden aangepast op basis ven een elastische botsing van twee bollen.'''
        distance = np.linalg.norm(self.position - other.position)
        if distance < self.radius + other.radius:
            normal = (self.position - other.position) / distance # vector normaal op oppervlakken beide deeltjes
            relative_velocity = self.velocity - other.velocity                  
            velocity_along_normal = np.dot(relative_velocity, normal)
            if velocity_along_normal > 0:
                return  # deeltjes bewegen van elkaar vandaan, dus geen botsing
            delta = (2 * velocity_along_normal) / (self.mass + other.mass)
            self.velocity -= delta * other.mass * normal
            other.velocity += delta * self.mass * normal

    @property
    def momentum(self):
        return self.mass * self.velocity
        
class ControlVol:
    def __init__(self, size, num_atoms, resize_speed):
        self.size = np.array(size, dtype=float)
        self.resize_speed = np.array(resize_speed, dtype=float)
        self.atoms = [Atom(mass=1.0, radius=0.1, position=np.multiply(np.random.rand(DIMENSION), self.size), velocity=np.random.randn(DIMENSION)) for _ in range(num_atoms)]
        self.times = []
        self.volumes = []
        self.temperatures = []
        self.momenta = []
        self.pressures = []
        self.works = []
        
    def check_wall_collisions(self):
        ''' functie die bepaalt of er atomen zijn die met de wanden botsen '''
        for atom in self.atoms:
            for i in range(DIMENSION):
                if atom.position[i] < 0:
                    atom.velocity[i] *= -1
                    # Hier kan de thermostaat ingebouwd
                    # atom.velocity *= math.sqrt(self.thermostat / self.temperature)
                elif atom.position[i] > self.size[i]:
                    atom.velocity[i] *= -1
                    atom.velocity[i] += 2 * self.resize_speed[i]  # pas snelheid aan ivm zuiger
    
    def move(self):
        ''' verplaatsing zuiger, atomen uitvoeren alle botsingen en bepaling alle grootheden voor logboek '''
        self.size += self.resize_speed * DT
        for atom in self.atoms:
            atom.move()
        for atom, other in combinations(self.atoms, 2):
            atom.check_atom_collision(other)
        self.check_wall_collisions()
        if self.times == []:
            self.times.append(DT)
            self.works.append(self.dwork)
            self.pressures.append(self.pressure)
        else:
            self.times.append(self.times[-1] + DT)
            self.works.append(self.works[-1] + self.dwork)
            self.pressures.append(0.9 * self.pressures[-1] + 0.1 * self.pressure)
        self.volumes.append(self.volume)
        self.temperatures.append(self.temperature)
        self.momenta.append(self.momentum)

    @property
    def volume(self):
        return math.prod(self.size)
    
    @property 
    def area(self):
        return 2 * sum(self.volume / self.size)
    
    @property
    def temperature(self):
        en = 0.0
        for atom in self.atoms:
            en += 0.5 * atom.mass * np.dot(atom.velocity, atom.velocity)
        return en / len(self.atoms)
    
    @property
    def momentum(self):
        return sum(atom.momentum for atom in self.atoms)

    @property 
    def impulse(self):
        ''' Deze functie geeft de stoot van de atomen op de muren. Dit is een twee-dimensionele array: de eerste index geeft x, y of z-richting weer. De tweede index geeft aan: bij 0 de wand die door de oorsprong gaat en stilstaat, bij 1 de wand die niet door de oorsprong gaat en met resize_speed een snelheid kan hebben '''
        J = np.zeros((DIMENSION, 2), dtype=float)
        for atom in self.atoms:
            for i in range(DIMENSION):
                if atom.position[i] < 0:
                    J[i, 0] += 2 * atom.mass * atom.velocity[i]
                elif atom.position[i] > self.size[i]:
                    J[i, 1] -= 2 * atom.mass * atom.velocity[i]
                    # let op: de stoot is eigenlijk het verschil tussen de snelheid voor de botsing met de wand
                    # en de snelheid erna. Die zijn verschillend door de botsing met de wand, dus de correctie is:
                    J[i, 1] += 2 * atom.mass * self.resize_speed[i]
        return J

    @property 
    def pressure(self):
        return np.sum(self.impulse) / self.area
    
    @property 
    def dwork(self):
        return np.dot(self.impulse[:, 1], self.resize_speed) / DT
    
def init():
    ax1.set_xlim(0, cv.size[0])
    ax1.set_ylim(0, cv.size[1])
    ax1.set_aspect('equal')
    ax2.set_xlim(0, cv.volume)
    ax2.set_ylim(0, cv.pressure)
    ax2.set_xlabel('Volume')
    ax2.set_ylabel('Pressure')
    ax3.set_xlim(0, cv.volume)
    ax3.set_ylim(0, cv.temperature)
    ax3.set_xlabel('Volume')
    ax3.set_ylabel('Temp')
    fig.tight_layout() 

def animate(frame):
    cv.move()

    ax2.set_xlim(0, max(cv.volumes))
    ax2.set_ylim(0, max(cv.pressures))
    pV_plot.set_data(cv.volumes, cv.pressures)

    ax3.set_xlim(0, max(cv.volumes))
    ax3.set_ylim(0, max(cv.temperatures))
    VT_plot.set_data(cv.volumes, cv.temperatures)

    if cv.size[0] < STARTSIZE * 0.3 or cv.size[0] > STARTSIZE:
        cv.resize_speed *= -1
  
    return pV_plot, VT_plot

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12,4))
cv = ControlVol(np.ones(DIMENSION) * STARTSIZE, NUMBER, np.ones(DIMENSION) * -0.1)
for atom in cv.atoms:
    ax1.add_patch(atom.circle)
    
pV_plot, = ax2.plot(cv.volumes, cv.pressures, 'r-')
VT_plot, = ax3.plot(cv.volumes, cv.temperatures, 'b-')


ani = animation.FuncAnimation(fig, animate, init_func=init, frames=FRAMES, interval=50, blit=False, repeat=True)
plt.show()
# ani.save('ani.gif', writer='pillow', fps=30, dpi=100)
