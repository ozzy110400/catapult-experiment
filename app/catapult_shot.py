from typing import Callable

import math
import numpy as np
import matplotlib.pyplot as plt


def calculate_bungee_diff_squares(
        rest_length: float,
        bungee_position: float,
        pin_elevation: float,
        axle_distance: float,
        release_angle: float,
        firing_angle: float
) -> float:
    """
    This function calculates difference between bungee states
    (s_release^2 - s_firing^2) from the formula for energy: delta_E = 1/2 * D * (s_release^2 - s_firing^2)

    :param rest_length: float, in meters
    :param bungee_position: float, in meters
    :param pin_elevation: float, in meters
    :param axle_distance: float, in meters
    :param release_angle: float, in degrees
    :param firing_angle: float, in degrees

    :return: squares_diff: float, (s_release^2 - s_firing^2)
    """

    x_release, y_release = get_arm_point(
        axle_distance=axle_distance,
        point_elevation=bungee_position,
        arm_angle=release_angle
    )
    # print(f'x_release: {x_release} \n y_release: {y_release}')

    x_firing, y_firing = get_arm_point(
        axle_distance=axle_distance,
        point_elevation=bungee_position,
        arm_angle=firing_angle
    )
    # print(f'x_firing: {x_firing} \n y_firing: {y_firing}')

    x_pin = 0.0
    y_pin = pin_elevation

    length_release = math.sqrt((x_pin - x_release) ** 2 + (y_pin - y_release) ** 2) + math.sqrt(x_pin**2 + y_pin**2)
    length_firing = math.sqrt((x_pin - x_firing) ** 2 + (y_pin - y_firing) ** 2) + math.sqrt(x_pin**2 + y_pin**2)

    s_release = (length_release > rest_length) * (length_release - rest_length)
    s_firing = (length_firing > rest_length) * (length_firing - rest_length)
    # print(length_release, length_firing)
    return (s_release ** 2) - (s_firing ** 2)


def calculate_omega(
        spring_constant: float,
        difference_s_squares: float,
        mass_payload: float,
        mass_distance: float,
        arm_moment_of_inertia: float
) -> float:
    """
    This function calculates angular velocity of the catapult arm.

    :param spring_constant: float, in N/m
    :param difference_s_squares: float, in m^2
    :param mass_payload: float, in kg
    :param mass_distance: float, in m
    :param arm_moment_of_inertia: float, in kg*m^2

    :return: omega: float, in rad/s
    """
    spring_energy = spring_constant * difference_s_squares
    kinetic_divisor = mass_payload * (mass_distance ** 2) + arm_moment_of_inertia
    # print(difference_s_squares, spring_energy, kinetic_divisor)
    omega = math.sqrt(spring_energy/kinetic_divisor)
    return omega


def calculate_mass_starting_angle(firing_angle: float) -> float:
    """
    This function returns starting angle of the independent motion of the ball bass
    :param firing_angle: float, in degrees
    :return: starting_angle: float, in degrees
    """
    starting_angle = firing_angle - 90
    return starting_angle


def get_arm_point(
        axle_distance: float,
        point_elevation: float,
        arm_angle: float
) -> tuple[float, float]:
    """
    This function returns a point as (x, y) on the arm lying 'point_elevation' meters from the axle
    :param axle_distance: float, in m
    :param point_elevation: float, in m
    :param arm_angle: float, in degrees
    :return: (x, y): tuple[float, float], in m
    """
    x = - axle_distance + math.cos(math.radians(arm_angle)) * point_elevation
    y = math.sin(math.radians(arm_angle)) * point_elevation
    # print("get arm pos: ", axle_distance, point_elevation, arm_angle, x, y)
    return x, y


def get_speed_components(velocity: float, angle: float) -> tuple[float, float]:
    """
    This function returns velocity projections' absolute values on x and y axes
    :param velocity: float, in m/s
    :param angle: float, in degrees
    :return: speed_x, speed_y: float, in m/s
    """
    speed_x = velocity * math.cos(math.radians(angle))
    speed_y = velocity * math.sin(math.radians(angle))
    return speed_x, speed_y


def calculate_time_to_ground(acceleration_y: float, speed_y_start: float, position_y_start: float) -> float:
    """
    Return time it takes the ball to hit the ground
    :param acceleration_y: float, in m/s^2
    :param speed_y_start: float, in m/s
    :param position_y_start: float, in m
    :return: time: float, s
    """
    discriminant = (speed_y_start ** 2) - 2 * position_y_start * acceleration_y
    assert discriminant >= 0, "Check your vertical acceleration value (should be <0)."
    time_1 = 1 / acceleration_y * (-speed_y_start + math.sqrt(discriminant))
    time_2 = 1 / acceleration_y * (-speed_y_start - math.sqrt(discriminant))
    # print(time_1, time_2)
    assert time_1 < 0 or time_2 < 0, "Make sure the mass starts moving above the ground."
    return time_2


def get_y_of_t(position_y_start: float, speed_y_start: float, acceleration_y: float) -> Callable[[float], float]:
    """
    Returns a function y(t) for the mass height
    :param position_y_start: float, in m
    :param speed_y_start: float, in m/s
    :param acceleration_y: float, in m/s^2
    :return: y(t): Callable[[float], float], in [[s], m]
    """
    def y(t: float) -> float:
        return 1/2 * acceleration_y * (t**2) + speed_y_start * t + position_y_start

    return y


def get_y_of_x(
        acceleration_y: float,
        speed_start: tuple[float, float],
        point_start: tuple[float, float]
) -> Callable[[float], float]:
    """
    Returns a function y(x) for the mass flight trajectory
    :param acceleration_y: float, in m/s^2
    :param speed_start: tuple[float, float], in m/s
    :param point_start: tuple[float, float], in m
    :return: y(x): Callable[[float], float], in [[m], m]
    """
    def y(x: float) -> float:
        a = 1/2 * acceleration_y / (speed_start[0]**2)
        b = speed_start[1] / speed_start[0] - acceleration_y * point_start[0] / (speed_start[0]**2)
        c = point_start[1] - speed_start[1] / speed_start[0] * point_start[0] + 1/2 * acceleration_y * (point_start[0]**2) / (speed_start[0]**2)
        return a * (x**2) + b * x + c

    return y


def calculate_max_height(
        start_y_position: float,
        start_y_speed: float,
        acceleration_y: float
) -> float:
    max_height = start_y_position - 1/2 * (start_y_speed**2) / acceleration_y
    return max_height


if __name__ == "__main__":
    g = 9.81                            # m/s^2         - Free fall acceleration
    D = 85.4                            # N/m           - Spring constant
    J = 1/3 * 0.156 * 0.346 ** 2        # kg*m^2        - Moment of inertia of the catapult arm
    m_cup = 0.027                       # kg            - Cup mass
    m_ball = 0.00267                    # kg            - Ball mass
    m = m_ball + m_cup                  # kg            - Total mass of cup and ball

    axle_distance = 0.158                       # m             - Distance from arm till rubber band
    bungee_length_no_load = 0.310 + 0.055       # m             - Bungee length at rest
    height_offset = 0.044                       # m             - Distance of the pivot points from the ground

    pin_elevation = 0.217               # m             - A = 0.126 m
    bungee_position = 0.185             # m             - 1 = 0.150 m
    cup_elevation = 0.325               # m             - 6 = 0.325 m
    firing_angle = 180 - 36             # degrees
    release_angle = 172.5               # degrees

    diff_s_squares = calculate_bungee_diff_squares(
        rest_length=bungee_length_no_load,
        bungee_position=bungee_position,
        pin_elevation=pin_elevation,
        axle_distance=axle_distance,
        release_angle=release_angle,
        firing_angle=firing_angle
    )

    omega = calculate_omega(
        spring_constant=D,
        difference_s_squares=diff_s_squares,
        mass_payload=m,
        mass_distance=cup_elevation,
        arm_moment_of_inertia=J
    )

    # print(f'omega is: {omega}')
    velocity_start = omega * cup_elevation
    point_start = get_arm_point(
        axle_distance=axle_distance,
        point_elevation=cup_elevation,
        arm_angle=firing_angle
    )

    point_start = (point_start[0], point_start[1] + height_offset)
    angle_start = calculate_mass_starting_angle(firing_angle=firing_angle)
    speed_x_start, speed_y_start = get_speed_components(velocity=velocity_start, angle=angle_start)

    time_ground = calculate_time_to_ground(
        acceleration_y=-g,
        speed_y_start=speed_y_start,
        position_y_start=point_start[1]
    )

    point_ground = (point_start[0] + speed_x_start * time_ground, 0.0)
    time_to_reach_max_height = speed_y_start / g
    func_y_of_t = get_y_of_t(position_y_start=point_start[1], speed_y_start=speed_y_start, acceleration_y=-g)
    assert func_y_of_t(0.0) == point_start[1], "Starting heights are different."

    func_y_of_x = get_y_of_x(
        acceleration_y=-g,
        speed_start=(speed_x_start, speed_y_start),
        point_start=point_start
    )

    ts = np.linspace(0.0, time_ground, num=420)
    xs = np.linspace(point_start[0], point_ground[0], num=420)
    yts = [func_y_of_t(t) for t in ts]
    yxs = [func_y_of_x(x) for x in xs]

    # print(func_y_of_x(0))
    # print(point_start[1])
    # print(point_ground[0])

    fig, ax = plt.subplots()
    ax.grid(alpha=0.5)
    ax.plot(ts, yts)
    ax.plot(xs, yxs)
    ax.axhline(y=0.0, color='r', linestyle='-')
    plt.show()
