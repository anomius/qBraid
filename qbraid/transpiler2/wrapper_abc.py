"""CircuitWrapper Class"""

from abc import abstractmethod

from typing import Tuple

from cirq import Circuit

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import UnsupportedCircuitError
from qbraid.transpiler2.exceptions import CircuitConversionError
from qbraid.transpiler2.conversions import convert_from_cirq, convert_to_cirq


class CircuitWrapper:
    """Abstract class for qbraid circuit wrapper objects.

    Note: The circuit wrapper object keeps track of abstract parameters and qubits using an
    intermediate representation. Qubits are stored simplhy as integers, and abstract parameters
    are stored as a :class:`qbraid.transpiler.parameter.ParamID` object, which stores an index in
    addition to a name. All other objects are transpiled directly when the
    :meth:`qbraid.transpiler.CircuitWrapper.transpile` method is called.

    Attributes:
        circuit: the underlying circuit object that has been wrapped
        qubits (List[int]): list of integers which represent all the qubits in the circuit,
            typically stored sequentially
        params: (Iterable): list of abstract paramaters in the circuit, stored as
            :class:`qbraid.transpiler.parameter.ParamID` objects
        num_qubits (int): number of qubits in the circuit
        depth (int): the depth of the circuit
        package (str): the package with which the underlying circuit was cosntructed

    """

    def __init__(self, circuit):

        self._circuit = circuit
        self._qubits = []
        self._num_qubits = 0
        self._num_clbits = 0
        self._depth = 0
        self._params = []
        self._input_param_mapping = {}
        self._package = None

    @property
    def circuit(self):
        """Return the underlying circuit that has been wrapped."""
        return self._circuit

    @property
    def qubits(self):
        """Return the qubits acted upon by the operations in this circuit"""
        return self._qubits

    @property
    def num_qubits(self):
        """Return the number of qubits in the circuit."""
        return self._num_qubits

    @property
    def num_clbits(self):
        """Return the number of classical bits in the circuit."""
        return self._num_clbits

    @property
    def depth(self):
        """Return the circuit depth (i.e., length of critical path)."""
        return self._depth

    @property
    def params(self):
        """Return the circuit parameters. Defaults to None."""
        return self._params

    @property
    def input_param_mapping(self):
        """Return the input parameter mapping. Defaults to None."""
        return self._input_param_mapping
    
    @property
    def package(self):
        """Return the original package of the wrapped circuit."""
        return self._package


    @abstractmethod
    def convert_to_cirq(self, circuit: QPROGRAM) -> Tuple[Circuit, str]:
        """Converts any valid input circuit to a Cirq circuit.
        Args:
            circuit: Any quantum circuit object supported by qbraid.transpiler.
                    See qbraid.transpiler.SUPPORTED_PROGRAM_TYPES.
        Returns:
            circuit: Cirq circuit equivalent to input circuit.
            input_circuit_type: Type of input circuit represented by a string.
        """

    @abstractmethod
    def convert_from_cirq(self, circuit: Circuit, conversion_type: str) -> QPROGRAM:
        """Converts a Cirq circuit to a type specified by the conversion type.
        Args:
            circuit: Cirq circuit to convert.
            conversion_type: String specifier for the converted circuit type.
        """

    def transpile(self, conversion_type, *args, **kwargs):
        """Transpile a qbraid quantum circuit wrapper object to quantum circuit object of type
         specified by ``conversion_type``.

        Args:
            conversion_type (str): target package

        Returns:
            quantum circuit object of type specified by ``package``

        Raises:
            UnsupportedCircuitError: If the input circuit is not supported, or
                conversion to circuit of type ``conversion_type`` is not unsupported.
            CircuitConversionError: If the input circuit could not be converted to a
                circuit of type ``conversion_type``.

        """
        if conversion_type == self.package:
            return self.circuit
        if conversion_type in SUPPORTED_PROGRAM_TYPES:
            try:
                # cirq_circuit, _ = self.convert_to_cirq(self.circuit)
                cirq_circuit, _ = convert_to_cirq(self.circuit)
            except Exception:
                raise CircuitConversionError(
                    "Circuit could not be converted to a Cirq circuit. "
                    "This may be because the circuit contains custom gates or "
                    f"Pragmas (pyQuil). \n\nProvided circuit has type {type(self.circuit)} "
                    f"and is:\n\n{self.circuit}\n\nCircuit types supported by the "
                    f"qbraid.transpiler are \n{SUPPORTED_PROGRAM_TYPES}."
                )
            try:
                # converted_circuit = self.convert_from_cirq(cirq_circuit, conversion_type)
                converted_circuit = convert_from_cirq(cirq_circuit, conversion_type)
            except Exception:
                raise CircuitConversionError(
                    f"Circuit could not be converted from a Cirq type to a "
                    f"circuit of type {conversion_type}."
                )
            return converted_circuit

        raise UnsupportedCircuitError(
            f"Conversion to circuit of type {conversion_type} is "
            "unsupported. \nCircuit types supported by the "
            f"qbraid.transpiler = {SUPPORTED_PROGRAM_TYPES}"
        )
