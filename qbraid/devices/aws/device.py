"""
Module defining BraketDeviceWrapper Class

"""
import math

# import warnings
from typing import TYPE_CHECKING

from braket.aws import AwsDevice

from qbraid.api.config_user import get_config
from qbraid.api.job_api import init_job
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError

from .job import BraketQuantumTaskWrapper

if TYPE_CHECKING:
    import braket

    import qbraid


class BraketDeviceWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(self, **kwargs):
        """Create a BraketDeviceWrapper."""

        super().__init__(**kwargs)
        bucket = get_config("s3_bucket", "AWS")
        folder = get_config("s3_folder", "AWS")
        self._s3_location = (bucket, folder)
        self._arn = self._obj_arg

    def _get_device(self):
        """Initialize an AWS device."""
        try:
            return AwsDevice(self._obj_arg)
        except ValueError as err:
            raise DeviceError("Device not found") from err

    def _vendor_compat_run_input(self, run_input):
        return run_input

    @property
    def status(self) -> "qbraid.devices.DeviceStatus":
        """Return the status of this Device.

        Returns:
            The status of this Device
        """
        if self.vendor_dlo.status == "OFFLINE":
            return DeviceStatus.OFFLINE
        return DeviceStatus.ONLINE

    def run(
        self, run_input: "braket.circuits.Circuit", *args, **kwargs
    ) -> "qbraid.device.aws.BraketQuantumTaskWrapper":
        """Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            shots (int): The number of times to run the task on the device.

        Returns:
            The job like object for the run.

        """
        run_input, qbraid_circuit = self._compat_run_input(run_input)
        # if "shots" not in kwargs and not run_input.result_types:
        #     warnings.warn(
        #         "No result types specified for circuit and shots=0. See "
        #         "`braket.circuit.result_types`. Defaulting to shots=1024 and continuing run.",
        #         UserWarning,
        #     )
        #     kwargs["shots"] = 1024
        aws_quantum_task = self.vendor_dlo.run(run_input, self._s3_location, *args, **kwargs)
        metadata = aws_quantum_task.metadata()
        shots = 0 if "shots" not in metadata else metadata["shots"]
        vendor_job_id = aws_quantum_task.metadata()["quantumTaskArn"]
        job_id = init_job(vendor_job_id, self, qbraid_circuit, shots)
        return BraketQuantumTaskWrapper(
            job_id, vendor_job_id=vendor_job_id, device=self, vendor_jlo=aws_quantum_task
        )

    def estimate_cost(self, circuit: "braket.circuits.Circuit", shots=1024):
        """Estimate the cost of running a quantum task on this device.

        Args:
            circuit: The circuit to run on the device. Can be a Braket, Qiskit, or Cirq circuit.
            shots (int, optional): Number of shots to run on device. Defaults to 1024.

        Raises:
            DeviceError: Throws error if circuit is not specified.

        Returns:
            he estimated cost of running the circuit on the device.

        """
        # TODO: Connect/ensure consistency with the cost estimator in the API.
        if circuit is None:
            raise DeviceError("Circuit must be specified")
        _, qbraid_circuit = self._compat_run_input(circuit)
        estimate = 0
        task_price = 0.3
        device = self._get_device()
        device_prop_dict = device.properties.dict()
        price = device_prop_dict["service"]["deviceCost"]["price"]
        # Simulators
        if device.name in ["SV1", "DM1"]:
            estimate = price * qbraid_circuit.num_qubits + math.exp(shots / 1000)
        elif device.name == "TN1":
            estimate = price * qbraid_circuit.num_qubits + math.exp(shots / 1000)
        # QPUs
        else:
            estimate = price * shots + task_price
        return estimate
