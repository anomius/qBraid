from typing import Any, Callable

from numpy import ndarray

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import QbraidError, UnsupportedCircuitError


class UnitaryCalculationError(QbraidError):
    pass


def to_unitary(circuit: QPROGRAM, ensure_contiguous=False) -> ndarray:
    """Calculates the unitary of any valid input circuit.

    Args:
        circuit: Any quantum circuit object supported by qBraid.
        ensure_contiguous: If True, calculates unitary using contiguous qubit indexing

    Raises:
        UnsupportedCircuitError: If the input circuit is not supported.

    Returns:
        numpy.ndarray: Matrix representation of the input circuit.
    """
    to_unitary_function: Callable[[Any], ndarray]

    try:
        package = circuit.__module__
    except AttributeError:
        raise UnsupportedCircuitError("Could not determine the package of the input circuit.")

    if "qiskit" in package:
        from qbraid.interface.qbraid_qiskit import unitary_from_qiskit

        to_unitary_function = unitary_from_qiskit
    elif "cirq" in package:
        from qbraid.interface.qbraid_cirq import unitary_from_cirq

        to_unitary_function = unitary_from_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket import unitary_from_braket

        to_unitary_function = unitary_from_braket
    else:
        raise UnsupportedCircuitError(
            f"Circuit from module {package} is not supported.\n\n"
            f"Circuit types supported by qBraid are \n{SUPPORTED_PROGRAM_TYPES}"
        )

    try:
        unitary = to_unitary_function(circuit, ensure_contiguous=ensure_contiguous)
    except Exception:
        raise UnitaryCalculationError("Unitary could not be calculated from given circuit.")

    return unitary
