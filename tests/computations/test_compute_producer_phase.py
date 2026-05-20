# Copyright 2026 Joseph Ibrahim
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Stub tests for compute_producer_phase. Bodies arrive in Session 03."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.computations.compute_producer_phase import compute_producer_phase
from src.schemas import ProducerPhase


class TestComputeProducerPhase:
    def test_family_lockout(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 23, 12, 0), ProducerPhase.MIDDAY)

    def test_morning(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 20, 10, 0), ProducerPhase.MORNING)

    def test_midday(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 20, 13, 0), ProducerPhase.MIDDAY)

    def test_evening(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 20, 15, 0), ProducerPhase.EVENING)

    def test_weekly_monday(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 18, 9, 0), ProducerPhase.WEEKLY_MONDAY)

    def test_weekly_friday(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 5, 22, 16, 0), ProducerPhase.WEEKLY_FRIDAY)

    def test_monthly(self):
        with pytest.raises(NotImplementedError, match="Session 03"):
            compute_producer_phase(datetime(2026, 6, 1, 10, 0), ProducerPhase.MONTHLY)
