import pytest
import tensorflow as tf
import numpy as np

from zfit import ztf
import zfit.core.basepdf
from zfit.core.limits import Range
from zfit.minimizers.minimizer_minuit import MinuitMinimizer
import zfit.pdfs.dist_tfp
from zfit.pdfs.dist_tfp import Normal
from zfit.pdfs.basic import Gauss
from zfit.core.parameter import FitParameter
import zfit.settings
from zfit.core.loss import _unbinned_nll_tf, UnbinnedNLL

mu_true = 1.2
sigma_true = 4.1

test_values_np = np.random.normal(loc=mu_true, scale=sigma_true, size=1000)

low, high = -24.3, 28.6
mu1 = FitParameter("mu1", ztf.to_real(mu_true) - 0.2, mu_true - 1., mu_true + 1.)
sigma1 = FitParameter("sigma1", ztf.to_real(sigma_true) - 0.3, sigma_true - 2., sigma_true + 2.)
mu2 = FitParameter("mu2", ztf.to_real(mu_true) - 0.2, mu_true - 1., mu_true + 1.)
sigma2 = FitParameter("sigma2", ztf.to_real(sigma_true) - 0.3, sigma_true - 2., sigma_true + 2.)

# HACK
# Gauss = Normal
# HACK END
mu_constr = Gauss(1.6, 0.2, name="mu_constr")
sigma_constr = Gauss(3.8, 0.2, name="sigma_constr")

gaussian1 = Gauss(mu1, sigma1, name="gaussian1")
gaussian2 = Gauss(mu2, sigma2, name="gaussian2")

init = tf.global_variables_initializer()


def test_unbinned_nll():
    with tf.Session() as sess:
        sess.run(init)
        with mu_constr.temp_norm_range((-np.infty, np.infty)):
            with sigma_constr.temp_norm_range((-np.infty, np.infty)):
                test_values = tf.constant(test_values_np)
                # nll = _unbinned_nll_tf(pdf=gaussian1, data=test_values, fit_range=(-np.infty, np.infty))
                nll_class = UnbinnedNLL(pdf=gaussian1, data=test_values, fit_range=(-np.infty, np.infty))
                # nll_eval = sess.run(nll)
                minimizer = MinuitMinimizer(loss=nll_class)
                status = minimizer.minimize(params=[mu1, sigma1], sess=sess)
                params = status.get_parameters()
                # print(params)
                assert params[mu1.name]['value'] == pytest.approx(np.mean(test_values_np), rel=0.005)
                assert params[sigma1.name]['value'] == pytest.approx(np.std(test_values_np), rel=0.005)

                # with constraints
                sess.run(init)

                nll_class = UnbinnedNLL(pdf=gaussian2, data=test_values, fit_range=(-np.infty, np.infty),
                                        constraints={mu2: mu_constr,
                                                     sigma2: sigma_constr})

                minimizer = MinuitMinimizer(loss=nll_class)
                status = minimizer.minimize(params=[mu2, sigma2], sess=sess)
                params = status.get_parameters()

                assert params[mu2.name]['value'] > np.mean(test_values_np)
                assert params[sigma2.name]['value'] < np.std(test_values_np)

                print(status)


#
# def true_gaussian_func(x):
#     return np.exp(- (x - mu_true) ** 2 / (2 * sigma_true ** 2))

def test_add():
    param1 = FitParameter("param1", 1.)
    param2 = FitParameter("param2", 2.)

    pdfs = [0] * 4
    pdfs[0] = Gauss(param1, 4)
    pdfs[1] = Gauss(param2, 5)
    pdfs[2] = Gauss(3, 6)
    pdfs[3] = Gauss(4, 7)

    datas = [0] * 4
    datas[0] = ztf.constant(1.)
    datas[1] = ztf.constant(2.)
    datas[2] = ztf.constant(3.)
    datas[3] = ztf.constant(4.)

    ranges = [0] * 4
    ranges[0] = (1, 4)
    ranges[1] = Range.from_limits((2, 5), dims=(0,))
    ranges[2] = Range.from_limits((3, 6), dims=(0,))
    ranges[3] = Range.from_limits((4, 7), dims=(0,))

    constraint1 = {param1: Gauss(1, 0.5)}
    constraint2 = {param2: Gauss(2, 0.25)}
    merged_contraints = constraint1.copy()
    merged_contraints.update(constraint2)

    nll1 = UnbinnedNLL(pdf=pdfs[0], data=datas[0], fit_range=ranges[0], constraints=constraint1)
    nll2 = UnbinnedNLL(pdf=pdfs[1], data=datas[1], fit_range=ranges[1], constraints=constraint2)
    nll3 = UnbinnedNLL(pdf=[pdfs[2], pdfs[3]], data=[datas[2], datas[3]], fit_range=[ranges[2], ranges[3]])

    simult_nll = nll1 + nll2 + nll3

    assert simult_nll.pdf == pdfs
    assert simult_nll.data == datas

    ranges[0] = Range.from_limits(ranges[0], dims=(0,))  # for comparison, Range can only compare with Range
    assert simult_nll.fit_range == ranges

    assert simult_nll.constraints == merged_contraints