#!/usr/bin/env python

import numpy as np
import pytest

from olympus.surfaces import Surface, get_surfaces_list

CAT_SURFS = [
    "CatDejong",
    "CatAckley",
    "CatMichalewicz",
    "CatCamel",
    "CatSlope",
]
GMM_SURFS = [
    "Denali",
    "Everest",
    "K2",
    "Kilimanjaro",
    "Matterhorn",
    "MontBlanc",
    "GaussianMixture",
]
MOO_SURFS = ["MultFonseca", "MultViennet", "MultZdt1", "MultZdt2", "MultZdt3"]


def test_init():
    surface = Surface(kind="Dejong", param_dim=2)
    assert surface.kind == "Dejong"
    assert surface.param_dim == 2


def test_run_dejong():
    surface = Surface(kind="Dejong", param_dim=2)
    params = np.zeros(2) + 0.5
    values = surface.run(params)[0][0]
    assert values < 1e-7


def test_run_catdejong():
    surface = Surface(kind="CatDejong", param_dim=2, num_opts=21)
    params = ["x10", "x10"]
    values = surface.run(params)[0][0]
    assert values < 1e-7


@pytest.mark.parametrize("kind", get_surfaces_list())
def test_cont_surfaces(kind):
    if not kind in CAT_SURFS + MOO_SURFS:
        surface = Surface(kind=kind, param_dim=2)
        if kind not in GMM_SURFS:
            min_dicts = surface.minima
            for min_dict in min_dicts:
                params, value = min_dict["params"], min_dict["value"]
                calc_value = surface.run(params)[0][0]
                np.testing.assert_almost_equal(value, calc_value)


@pytest.mark.parametrize("kind", get_surfaces_list())
def test_cat_surfaces(kind):
    if kind in CAT_SURFS:
        surface = Surface(kind=kind, param_dim=2, num_opts=21)
        min_dicts = surface.minima
        for min_dict in min_dicts:
            params, value = min_dict["params"], min_dict["value"]
            calc_value = surface.run(params)[0][0]
            np.testing.assert_almost_equal(value, calc_value)


@pytest.mark.parametrize("kind", get_surfaces_list())
def test_moo_surfaces(kind):
    if kind in MOO_SURFS:
        surface = Surface(kind=kind, param_dim=2, value_dim=2)
        # TODO: implement the maxima and minima for the MOO surfaces
