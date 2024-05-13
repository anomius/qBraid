# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for Amazon Braket cost tracker interface

"""
import os
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from braket.aws.aws_device import AwsDevice
from braket.circuits import Circuit
from braket.tracking import Tracker

from qbraid.runtime.braket import BraketProvider
from qbraid.runtime.braket.device import _future_utc_datetime
from qbraid.runtime.braket.tracker import get_quantum_task_cost
from qbraid.runtime.exceptions import JobStateError

# Skip tests if AWS account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of AWS storage)"


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_simulator():
    """Test getting cost of quantum task run on an AWS simulator."""
    provider = BraketProvider()
    device = provider.get_device("arn:aws:braket:::device/quantum-simulator/amazon/sv1")
    circuit = Circuit().h(0).cnot(0, 1)

    with Tracker() as tracker:
        task = device.run(circuit, shots=2)
        task.result()

    expected = tracker.simulator_tasks_cost()
    calculated = get_quantum_task_cost(task.id, provider._get_aws_session())
    assert expected == calculated


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_cancelled(braket_most_busy, braket_circuit):
    """Test getting cost of quantum task that was cancelled."""
    if braket_most_busy is None:
        pytest.skip("No AWS QPU devices available")

    provider = BraketProvider()

    # AwsSession region must match device region
    region_name = AwsDevice.get_device_region(braket_most_busy.id)
    aws_session = provider._get_aws_session(region_name)

    qbraid_job = braket_most_busy.run(braket_circuit, shots=10)
    qbraid_job.cancel()

    task_arn = qbraid_job.id

    try:
        qbraid_job.wait_for_final_state(timeout=30)
        final_state_reached = True
    except JobStateError:
        final_state_reached = False

    # Based on whether final state was reached or not, proceed to verify expected outcomes
    if final_state_reached:
        # Verify cost is as expected when job reaches a final state
        cost = get_quantum_task_cost(task_arn, aws_session)
        assert cost == Decimal(0), f"Expected cost to be 0 when job is in a final state, got {cost}"
    else:
        # Verify the appropriate error is raised when job has not reached a final state
        with pytest.raises(ValueError) as exc_info:
            get_quantum_task_cost(task_arn, aws_session)

        expected_msg_partial = f"Task {task_arn} is not COMPLETED."
        assert expected_msg_partial in str(
            exc_info.value
        ), "Unexpected error message for non-final job state"


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_get_quantum_task_cost_region_mismatch(braket_most_busy, braket_circuit):
    """Test getting cost of quantum task raises value error on region mismatch."""
    if braket_most_busy is None:
        pytest.skip("No AWS QPU devices available")

    braket_device = braket_most_busy._device
    task = braket_device.run(braket_circuit, shots=10)
    task.cancel()

    task_arn = task.id
    task_region = task_arn.split(":")[3]
    other_region = "eu-west-2" if task_region == "us-east-1" else "us-east-1"

    provider = BraketProvider()
    aws_session = provider._get_aws_session(other_region)

    with pytest.raises(ValueError) as excinfo:
        get_quantum_task_cost(task_arn, aws_session)

    assert (
        str(excinfo.value)
        == f"AwsSession region {other_region} does not match task region {task_region}"
    )


@pytest.mark.parametrize(
    "hours, minutes, seconds, expected",
    [
        (1, 0, 0, "2024-01-01T01:00:00Z"),
        (0, 30, 0, "2024-01-01T00:30:00Z"),
        (0, 0, 45, "2024-01-01T00:00:45Z"),
    ],
)
def test_future_utc_datetime(hours, minutes, seconds, expected):
    """Test calculating future utc datetime"""
    with patch("qbraid.runtime.braket.device.datetime") as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 0, 0, 0)
        assert _future_utc_datetime(hours, minutes, seconds) == expected