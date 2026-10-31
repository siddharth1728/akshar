"""
SENSEFORGE M04: Probe Evolutionary Factory
Generates, mutates, crosses over, and simplifies experimental probe protocols.
"""

from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass

from senseforge.probes.actions import (
    ProbeAction,
    WaitAction,
    ObserveAction,
    PerturbAction,
    ReversePerturbAction,
    RepeatAction,
)
from senseforge.probes.genome import ProbeGenome


@dataclass(frozen=True)
class ProbeConstraints:
    max_sequence_length: int = 12
    max_duration: int = 60
    max_magnitude: float = 1.0
    max_energy: float = 25.0


class ProbeFactory:
    """Evolutionary operator engine for ProbeGenomes."""

    @classmethod
    def create_random_probe(
        cls,
        seed: int,
        allowed_action_channels: List[int],
        constraints: Optional[ProbeConstraints] = None,
        num_actions: int = 4
    ) -> ProbeGenome:
        """Generates a random valid probe within budget constraints."""
        c = constraints or ProbeConstraints()
        rng = np.random.default_rng(seed)
        actions: List[ProbeAction] = []
        current_dur = 0
        current_energy = 0.0

        n = min(max(2, num_actions), c.max_sequence_length)
        for _ in range(n):
            if current_dur >= c.max_duration or current_energy >= c.max_energy:
                break

            action_type = rng.choice(["wait", "perturb", "reverse_perturb", "repeat"])
            rem_dur = max(1, c.max_duration - current_dur)

            if action_type == "wait":
                steps = int(rng.integers(1, min(10, rem_dur) + 1))
                actions.append(WaitAction(steps=steps))
                current_dur += steps

            elif action_type in {"perturb", "reverse_perturb"}:
                ch = int(rng.choice(allowed_action_channels))
                mag = float(rng.uniform(0.1, c.max_magnitude))
                dur = int(rng.integers(1, min(5, rem_dur) + 1))
                e_cost = (mag ** 2) * dur
                if current_energy + e_cost > c.max_energy:
                    # Scale down magnitude to fit remaining energy
                    mag = float(np.sqrt(max(0.01, (c.max_energy - current_energy) / dur)))

                cls_act = PerturbAction if action_type == "perturb" else ReversePerturbAction
                actions.append(cls_act(channel=ch, magnitude=mag, duration=dur))
                current_dur += dur
                current_energy += (mag ** 2) * dur

            elif action_type == "repeat":
                ch = int(rng.choice(allowed_action_channels))
                mag = float(rng.uniform(0.1, c.max_magnitude * 0.8))
                dur = int(rng.integers(1, max(2, min(3, rem_dur // 2))))
                repeat_count = int(rng.integers(2, 4))
                total_rep_dur = dur * repeat_count
                if current_dur + total_rep_dur <= c.max_duration and current_energy + (mag ** 2) * total_rep_dur <= c.max_energy:
                    sub = PerturbAction(channel=ch, magnitude=mag, duration=dur)
                    actions.append(RepeatAction(action=sub, count=repeat_count))
                    current_dur += total_rep_dur
                    current_energy += (mag ** 2) * total_rep_dur
                else:
                    steps = int(rng.integers(1, min(5, rem_dur) + 1))
                    actions.append(WaitAction(steps=steps))
                    current_dur += steps

        if not actions:
            actions = [WaitAction(5)]

        return ProbeGenome(
            actions=actions,
            reproducibility_seed=seed,
            mutation_history=["RANDOM_INIT"],
        )

    @classmethod
    def mutate_magnitude(
        cls,
        probe: ProbeGenome,
        constraints: Optional[ProbeConstraints] = None,
        rng: Optional[np.random.Generator] = None
    ) -> ProbeGenome:
        """Perturbs action magnitudes with Gaussian noise."""
        c = constraints or ProbeConstraints()
        r = rng or np.random.default_rng()
        cloned = probe.clone()

        perturb_actions = [
            act for act in cloned.actions
            if isinstance(act, (PerturbAction, ReversePerturbAction)) or
               (isinstance(act, RepeatAction) and isinstance(act.action, (PerturbAction, ReversePerturbAction)))
        ]

        if perturb_actions:
            target = r.choice(perturb_actions)
            act_obj = target.action if isinstance(target, RepeatAction) else target
            jitter = float(r.normal(0.0, 0.15))
            new_mag = float(np.clip(act_obj.magnitude + jitter, 0.05, c.max_magnitude))
            act_obj.magnitude = new_mag
            cloned.mutation_history.append("MUTATE_MAGNITUDE")

        return cls.enforce_budget(cloned, c)

    @classmethod
    def mutate_timing(
        cls,
        probe: ProbeGenome,
        constraints: Optional[ProbeConstraints] = None,
        rng: Optional[np.random.Generator] = None
    ) -> ProbeGenome:
        """Perturbs action durations and delays."""
        c = constraints or ProbeConstraints()
        r = rng or np.random.default_rng()
        cloned = probe.clone()

        target = r.choice(cloned.actions)
        if isinstance(target, (WaitAction, ObserveAction)):
            delta = int(r.choice([-2, -1, 1, 2]))
            target._steps = max(1, min(20, target._steps + delta))
            cloned.mutation_history.append("MUTATE_TIMING")
        elif isinstance(target, (PerturbAction, ReversePerturbAction)):
            delta = int(r.choice([-1, 1]))
            target._duration = max(1, min(10, target._duration + delta))
            cloned.mutation_history.append("MUTATE_DURATION")

        return cls.enforce_budget(cloned, c)

    @classmethod
    def mutate_sequence(
        cls,
        probe: ProbeGenome,
        allowed_action_channels: List[int],
        constraints: Optional[ProbeConstraints] = None,
        rng: Optional[np.random.Generator] = None
    ) -> ProbeGenome:
        """Inserts, deletes, or swaps an action primitive in the sequence."""
        c = constraints or ProbeConstraints()
        r = rng or np.random.default_rng()
        cloned = probe.clone()

        op = r.choice(["insert", "delete", "swap"])
        if op == "insert" and len(cloned.actions) < c.max_sequence_length:
            ch = int(r.choice(allowed_action_channels))
            mag = float(r.uniform(0.1, c.max_magnitude))
            dur = int(r.integers(1, 4))
            new_act = PerturbAction(channel=ch, magnitude=mag, duration=dur) if r.random() < 0.6 else WaitAction(int(r.integers(2, 6)))
            idx = int(r.integers(0, len(cloned.actions) + 1))
            cloned.actions.insert(idx, new_act)
            cloned.mutation_history.append("MUTATE_INSERT_ACTION")

        elif op == "delete" and len(cloned.actions) > 1:
            idx = int(r.integers(0, len(cloned.actions)))
            cloned.actions.pop(idx)
            cloned.mutation_history.append("MUTATE_DELETE_ACTION")

        elif op == "swap" and len(cloned.actions) > 1:
            i, j = r.choice(len(cloned.actions), size=2, replace=False)
            cloned.actions[i], cloned.actions[j] = cloned.actions[j], cloned.actions[i]
            cloned.mutation_history.append("MUTATE_SWAP_ACTIONS")

        return cls.enforce_budget(cloned, c)

    @classmethod
    def crossover(
        cls,
        parent_a: ProbeGenome,
        parent_b: ProbeGenome,
        constraints: Optional[ProbeConstraints] = None,
        rng: Optional[np.random.Generator] = None
    ) -> Tuple[ProbeGenome, ProbeGenome]:
        """Crossover exchanging action subsequences between two parent probes."""
        c = constraints or ProbeConstraints()
        r = rng or np.random.default_rng()

        cut_a = int(r.integers(1, len(parent_a.actions))) if len(parent_a.actions) > 1 else 1
        cut_b = int(r.integers(1, len(parent_b.actions))) if len(parent_b.actions) > 1 else 1

        actions_a = [act.clone() for act in parent_a.actions[:cut_a]] + [act.clone() for act in parent_b.actions[cut_b:]]
        actions_b = [act.clone() for act in parent_b.actions[:cut_b]] + [act.clone() for act in parent_a.actions[cut_a:]]

        off_a = ProbeGenome(
            actions=actions_a if actions_a else [WaitAction(5)],
            reproducibility_seed=int(r.integers(0, 1_000_000)),
            parent_ids=(parent_a.genome_id, parent_b.genome_id),
            generation_number=max(parent_a.generation_number, parent_b.generation_number) + 1,
            mutation_history=["CROSSOVER"],
        )
        off_b = ProbeGenome(
            actions=actions_b if actions_b else [WaitAction(5)],
            reproducibility_seed=int(r.integers(0, 1_000_000)),
            parent_ids=(parent_a.genome_id, parent_b.genome_id),
            generation_number=max(parent_a.generation_number, parent_b.generation_number) + 1,
            mutation_history=["CROSSOVER"],
        )

        return cls.enforce_budget(off_a, c), cls.enforce_budget(off_b, c)

    @classmethod
    def simplify_probe(cls, probe: ProbeGenome) -> ProbeGenome:
        """
        Simplifies consecutive redundant actions (e.g. adjacent Wait steps).
        """
        cloned = probe.clone()
        simplified_actions: List[ProbeAction] = []

        for act in cloned.actions:
            if not simplified_actions:
                simplified_actions.append(act)
                continue

            last = simplified_actions[-1]
            if isinstance(last, WaitAction) and isinstance(act, WaitAction):
                # Merge wait steps
                simplified_actions[-1] = WaitAction(steps=last.duration + act.duration)
            elif isinstance(last, PerturbAction) and isinstance(act, PerturbAction) and last.channel == act.channel and abs(last.magnitude - act.magnitude) < 1e-4:
                # Merge identical adjacent perturbations
                simplified_actions[-1] = PerturbAction(channel=last.channel, magnitude=last.magnitude, duration=last.duration + act.duration)
            else:
                simplified_actions.append(act)

        cloned.actions = simplified_actions if simplified_actions else [WaitAction(5)]
        cloned.mutation_history.append("SIMPLIFY")
        return cloned

    @classmethod
    def enforce_budget(cls, probe: ProbeGenome, constraints: ProbeConstraints) -> ProbeGenome:
        """Truncates or clamps actions that exceed the hard budget constraints."""
        trimmed_actions: List[ProbeAction] = []
        cur_dur = 0
        cur_energy = 0.0

        for act in probe.actions:
            if len(trimmed_actions) >= constraints.max_sequence_length:
                break
            if cur_dur + act.duration > constraints.max_duration:
                # Truncate duration if possible
                rem = constraints.max_duration - cur_dur
                if rem > 0:
                    if isinstance(act, WaitAction):
                        trimmed_actions.append(WaitAction(steps=rem))
                        cur_dur += rem
                    elif isinstance(act, PerturbAction):
                        trimmed_actions.append(PerturbAction(channel=act.channel, magnitude=act.magnitude, duration=rem))
                        cur_dur += rem
                        cur_energy += (act.magnitude ** 2) * rem
                break

            if cur_energy + act.energy_cost > constraints.max_energy:
                # Energy ceiling reached
                rem_e = max(0.0, constraints.max_energy - cur_energy)
                if rem_e > 0.01 and isinstance(act, PerturbAction):
                    clamped_mag = float(np.sqrt(rem_e / act.duration))
                    trimmed_actions.append(PerturbAction(channel=act.channel, magnitude=clamped_mag, duration=act.duration))
                    cur_dur += act.duration
                    cur_energy += (clamped_mag ** 2) * act.duration
                break

            trimmed_actions.append(act)
            cur_dur += act.duration
            cur_energy += act.energy_cost

        probe.actions = trimmed_actions if trimmed_actions else [WaitAction(5)]
        return probe

