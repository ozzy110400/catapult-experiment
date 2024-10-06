from pydantic import BaseModel, computed_field


class SimulationConfig(BaseModel):
    g: float = 9.81                                             # m/s^2         - Free fall acceleration
    spring_constant: float = 85.4                               # N/m           - Spring constant
    moment_of_inertia: float = 1 / 3 * 0.156 * 0.346 ** 2       # kg*m^2        - Moment of inertia of the catapult arm
    cup_mass: float = 0.027                                     # kg            - Cup mass
    ball_mass: float = 0.00267                                  # kg            - Ball mass

    # Total mass is calculated in configured_shot.py module

    # @computed_field
    # @property
    # def m(self) -> float:
    #     return self.m_ball + self.m_cup                 # kg            - Total mass of cup and ball

    axle_distance: float = 0.158                        # m             - Distance from arm till rubber band
    bungee_length_no_load: float = 0.310 + 0.055        # m             - Bungee length at rest
    height_offset: float = 0.044                        # m             - Distance of the pivot points from the ground

    pin_elevation: float = 0.217                        # m             - A = 0.126 m
    bungee_position: float = 0.185                      # m             - 1 = 0.150 m
    cup_elevation: float = 0.325                        # m             - 6 = 0.325 m
    firing_angle: float = 180 - 36                      # degrees
    release_angle: float = 172.5                        # degrees


class FullSimulationConfig(SimulationConfig):
    # Delta properties
    delta_g: float = 0.0
    delta_spring_constant: float = 0.0
    delta_moment_of_inertia: float = 0.0
    delta_cup_mass: float = 0.0
    delta_ball_mass: float = 0.0

    delta_axle_distance: float = 0.0
    delta_bungee_length_no_load: float = 0.0
    delta_height_offset: float = 0.0

    delta_pin_elevation: float = 0.0
    delta_bungee_position: float = 0.0
    delta_cup_elevation: float = 0.0
    delta_firing_angle: float = 0.0
    delta_release_angle: float = 0.0

    lateral_deviation_angle: float = 0.0
