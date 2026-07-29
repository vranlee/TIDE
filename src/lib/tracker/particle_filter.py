# vim: expandtab:ts=4:sw=4
import numpy as np
import scipy.linalg

"""
Table for the 0.95 quantile of the chi-square distribution with N degrees of
freedom (contains values for N=1, ..., 9). Taken from MATLAB/Octave's chi2inv
function and used as Mahalanobis gating threshold.
"""
chi2inv95 = {
    1: 3.8415,
    2: 5.9915,
    3: 7.8147,
    4: 9.4877,
    5: 11.070,
    6: 12.592,
    7: 14.067,
    8: 15.507,
    9: 16.919}



class ParticleFilter(object):
    def __init__(self, num_particles=1000):
        self.num_particles = num_particles

    def initiate(self, measurement):
        """
        Create particles from an unassociated measurement.
        """
        mean_pos = measurement
        mean_vel = np.zeros_like(mean_pos)
        mean = np.concatenate([mean_pos, mean_vel])

        std = [
            2 * self._std_weight_position * measurement[2],
            2 * self._std_weight_position * measurement[3],
            2 * self._std_weight_position * measurement[2],
            2 * self._std_weight_position * measurement[3],
            10 * self._std_weight_velocity * measurement[2],
            10 * self._std_weight_velocity * measurement[3],
            10 * self._std_weight_velocity * measurement[2],
            10 * self._std_weight_velocity * measurement[3]]
        covariance = np.diag(np.square(std))

        # Generate particles around the mean
        particles = np.random.multivariate_normal(mean, covariance, self.num_particles)

        return particles

    def predict(self, particles):
        """
        Run particle filter prediction step.
        """
        std_pos = [
            self._std_weight_position * particles[:, 2],
            self._std_weight_position * particles[:, 3],
            self._std_weight_position * particles[:, 2],
            self._std_weight_position * particles[:, 3]]
        std_vel = [
            self._std_weight_velocity * particles[:, 2],
            self._std_weight_velocity * particles[:, 3],
            self._std_weight_velocity * particles[:, 2],
            self._std_weight_velocity * particles[:, 3]]
        sqr = np.square(np.concatenate([std_pos, std_vel]).T)

        motion_cov = np.diag(sqr)

        # Update particle positions based on the motion model
        particles[:, :4] = np.dot(particles[:, :4], self._motion_mat.T)

        # Add noise to particle positions
        particles[:, :4] += np.random.multivariate_normal(np.zeros(4), motion_cov, self.num_particles)

        return particles

    def update(self, particles, measurement):
        """
        Run particle filter correction step.
        """
        # Project particles to measurement space
        projected_particles = np.dot(self._update_mat, particles.T).T

        # Compute the Mahalanobis distance between particles and measurement
        innovation = measurement - projected_particles[:, :4]
        squared_maha = np.sum((innovation / self._std_weight_position) ** 2, axis=1)

        # Resample particles based on the likelihood of each particle
        weights = np.exp(-0.5 * squared_maha)
        weights /= np.sum(weights)
        indices = np.random.choice(np.arange(self.num_particles), size=self.num_particles, p=weights)

        resampled_particles = particles[indices]

        return resampled_particles
