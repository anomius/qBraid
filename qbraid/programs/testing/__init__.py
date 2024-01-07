# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing utility functions for testing quantum programs.

.. currentmodule:: qbraid.programs.testing

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   circuits_allclose
   assert_allclose_up_to_global_phase

"""
from .circuit_equality import assert_allclose_up_to_global_phase, circuits_allclose