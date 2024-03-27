import numpy as np
from scipy.special import gamma

def fit_Hebbian_p(Ss, Ps, s_avg, p0):
    # Step size (adjust for convergence):
    step_size = 1e-3

    # Derivative resolution:
    dp = 1e-10

    # Stopping criteria:
    dE_dp_min = 1e-6
    max_steps = 1e4

    # Make sure we only have unique strength values:
    Ss_unique, indices = np.unique(Ss, return_index=True)
    Ps_unique = np.zeros_like(Ss_unique)

    for i, idx in enumerate(indices):
        Ps_unique[i] = np.sum(Ps[Ss == Ss_unique[i]])

    # Make sure probabilities are normalized to one:
    Ps_unique /= np.sum(Ps_unique)

    # Initialize Hebbian probability:
    p = p0

    # Loop until max number of steps:
    for i in range(int(max_steps)):
        # Compute model probabilities:
        Ps_pred = gamma(Ss_unique + s_avg * (1/p - 1)) / gamma(Ss_unique + s_avg * (1/p - 1) + 1 + 1/p)
        inds_bad = np.concatenate([np.where(np.isnan(Ps_pred))[0], np.where(Ps_pred < np.finfo(float).eps)[0]])
        if inds_bad.size != 0:
            c = Ps_pred[inds_bad[0]-1] / Ss_unique[inds_bad[0]-1] ** (-(1 + 1/p))
            Ps_pred[inds_bad] = c * Ss_unique[inds_bad] ** (-(1 + 1/p))
        Ps_pred /= np.sum(Ps_pred)

        # Compute model probabilities slightly away from p (for derivative):
        p_der = p + dp
        Ps_der = gamma(Ss_unique + s_avg * (1/p_der - 1)) / gamma(Ss_unique + s_avg * (1/p_der - 1) + 1 + 1/p_der)
        inds_bad = np.concatenate([np.where(np.isnan(Ps_der))[0], np.where(Ps_der == 0)[0]])
        if inds_bad.size != 0:
            c = Ps_der[inds_bad[0]-1] / Ss_unique[inds_bad[0]-1] ** (-(1 + 1/p_der))
            Ps_der[inds_bad] = c * Ss_unique[inds_bad] ** (-(1 + 1/p_der))
        Ps_der /= np.sum(Ps_der)

        # Compute error:
        err = np.sqrt(np.sum((np.log(Ps_unique) - np.log(Ps_pred))**2))
        err_der = np.sqrt(np.sum((np.log(Ps_unique) - np.log(Ps_der))**2))

        # Compute gradient of error with respect to Hebbian probability:
        dE_dp = (err_der - err) / dp

        # Stop if derivative is small enough:
        if np.abs(dE_dp) < dE_dp_min:
            return p

        # Update Hebbian probability:
        p = p - step_size * dE_dp / np.sqrt(i + 1)

        # Stop if p becomes ill-defined:
        if p < 0:
            return 0
        elif p > 1:
            return 1

    return p

# Example usage:
# p_fit = fit_Hebbian_p(Ss, Ps, s_avg, p0)
