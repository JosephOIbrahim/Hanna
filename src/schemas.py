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
"""Hanna producer-rhythm schemas. Seed: ProducerPhase only (per NEXT.md option b)."""

from __future__ import annotations
from enum import IntEnum


class ProducerPhase(IntEnum):
    FAMILY_LOCKOUT = 0
    MORNING = 1
    MIDDAY = 2
    EVENING = 3
    WEEKLY_MONDAY = 4
    WEEKLY_FRIDAY = 5
    MONTHLY = 6
