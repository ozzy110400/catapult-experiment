from app.catapult_shot import calculate_bungee_diff_squares, calculate_omega, get_arm_point, \
    calculate_mass_starting_angle, get_speed_components, calculate_time_to_ground, calculate_max_height

import math


def simulate(experiment_setup: dict) -> dict:
    g = experiment_setup['g']
    D = experiment_setup['spring_constant']
    J = experiment_setup['moment_of_inertia']
    m_cup = experiment_setup['cup_mass']
    m_ball = experiment_setup['ball_mass']
    m = m_cup + m_ball

    axle_distance = experiment_setup['axle_distance']
    bungee_length_no_load = experiment_setup['bungee_length_no_load']
    height_offset = experiment_setup['height_offset']

    pin_elevation = experiment_setup['pin_elevation']
    bungee_position = experiment_setup['bungee_position']
    cup_elevation = experiment_setup['cup_elevation']
    firing_angle = experiment_setup['firing_angle']                                 # in degrees
    release_angle = experiment_setup['release_angle']                               # in degrees

    lateral_deviation_angle = experiment_setup['lateral_deviation_angle']           # in degrees

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

    velocity_start = omega * cup_elevation
    point_start = get_arm_point(
        axle_distance=axle_distance,
        point_elevation=cup_elevation,
        arm_angle=firing_angle
    )

    point_start = (point_start[0], point_start[1] + height_offset)
    angle_start = calculate_mass_starting_angle(firing_angle=firing_angle)
    speed_x_start, speed_y_start = get_speed_components(velocity=velocity_start, angle=angle_start)
    speed_x_start = speed_x_start * math.cos(math.radians(lateral_deviation_angle))
    speed_z_start = speed_x_start * math.sin(math.radians(lateral_deviation_angle))

    time_ground = calculate_time_to_ground(
        acceleration_y=-g,
        speed_y_start=speed_y_start,
        position_y_start=point_start[1]
    )

    point_ground = (point_start[0] + speed_x_start * time_ground, 0.0)
    x_coordinate_ground = point_ground[0]
    y_coordinate_ground = point_ground[1]
    z_coordinate_ground = speed_z_start * time_ground

    max_height = calculate_max_height(
        start_y_position=point_start[1],
        start_y_speed=speed_y_start,
        acceleration_y=-g
    )

    outputs_dict = {
        "x_ground": x_coordinate_ground,
        "y_ground": y_coordinate_ground,
        "z_ground": z_coordinate_ground,
        "max_height": max_height
    }

    return outputs_dict
