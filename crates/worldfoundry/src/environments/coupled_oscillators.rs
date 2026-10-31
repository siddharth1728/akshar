use crate::firewall::SimEnvironment;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;

pub struct CoupledOscillators {
    num_oscillators: usize,
    step_size: f64,
    step_count: u64,
    sim_time: f64,
    c_coupling: f64,
    k: Vec<f64>,
    beta: Vec<f64>,
    mu: Vec<f64>,
    positions: Vec<f64>,
    velocities: Vec<f64>,
}

impl CoupledOscillators {
    pub fn new(seed: u64, num_oscillators: usize, step_size: f64, coupling: f64) -> Self {
        let mut rng = ChaCha8Rng::seed_from_u64(seed);
        let n = num_oscillators;
        let mut k = Vec::with_capacity(n);
        let mut beta = Vec::with_capacity(n);
        let mut mu = Vec::with_capacity(n);
        let mut positions = Vec::with_capacity(n);
        let mut velocities = Vec::with_capacity(n);

        for _ in 0..n {
            k.push(rng.gen_range(0.5..2.5));
            beta.push(rng.gen_range(0.1..0.8));
            mu.push(rng.gen_range(0.05..0.3));
            positions.push(rng.gen_range(-0.5..0.5));
            velocities.push(rng.gen_range(-0.1..0.1));
        }

        Self {
            num_oscillators: n,
            step_size,
            step_count: 0,
            sim_time: 0.0,
            c_coupling: coupling,
            k,
            beta,
            mu,
            positions,
            velocities,
        }
    }

    fn compute_accelerations(&self, pos: &[f64], vel: &[f64], action: Option<&[f64]>) -> Vec<f64> {
        let n = self.num_oscillators;
        let mut acc = Vec::with_capacity(n);

        for i in 0..n {
            let left = if i == 0 { pos[n - 1] } else { pos[i - 1] };
            let right = if i == n - 1 { pos[0] } else { pos[i + 1] };
            let coupling_force = self.c_coupling * (left + right - 2.0 * pos[i]);

            let restorative = -self.k[i] * pos[i] - self.beta[i] * pos[i].powi(3);
            let damping = -self.mu[i] * (pos[i].powi(2) - 1.0) * vel[i];

            let mut a = restorative + damping + coupling_force;
            if let Some(act) = action {
                if i < act.len() {
                    a += act[i];
                }
            }
            acc.push(a);
        }
        acc
    }
}

impl SimEnvironment for CoupledOscillators {
    fn step(&mut self, action: Option<&[f64]>) {
        let dt = self.step_size;
        let n = self.num_oscillators;
        let p0 = self.positions.clone();
        let v0 = self.velocities.clone();

        // RK4 step
        let k1_v = self.compute_accelerations(&p0, &v0, action);
        let k1_p = v0.clone();

        let mut p_mid1 = vec![0.0; n];
        let mut v_mid1 = vec![0.0; n];
        for i in 0..n {
            p_mid1[i] = p0[i] + 0.5 * dt * k1_p[i];
            v_mid1[i] = v0[i] + 0.5 * dt * k1_v[i];
        }
        let k2_v = self.compute_accelerations(&p_mid1, &v_mid1, action);
        let k2_p = v_mid1;

        let mut p_mid2 = vec![0.0; n];
        let mut v_mid2 = vec![0.0; n];
        for i in 0..n {
            p_mid2[i] = p0[i] + 0.5 * dt * k2_p[i];
            v_mid2[i] = v0[i] + 0.5 * dt * k2_v[i];
        }
        let k3_v = self.compute_accelerations(&p_mid2, &v_mid2, action);
        let k3_p = v_mid2;

        let mut p_end = vec![0.0; n];
        let mut v_end = vec![0.0; n];
        for i in 0..n {
            p_end[i] = p0[i] + dt * k3_p[i];
            v_end[i] = v0[i] + dt * k3_v[i];
        }
        let k4_v = self.compute_accelerations(&p_end, &v_end, action);
        let k4_p = v_end;

        for i in 0..n {
            self.positions[i] = (p0[i] + (dt / 6.0) * (k1_p[i] + 2.0 * k2_p[i] + 2.0 * k3_p[i] + k4_p[i])).clamp(-20.0, 20.0);
            self.velocities[i] = (v0[i] + (dt / 6.0) * (k1_v[i] + 2.0 * k2_v[i] + 2.0 * k3_v[i] + k4_v[i])).clamp(-50.0, 50.0);
        }

        self.step_count += 1;
        self.sim_time += dt;
    }

    fn reset(&mut self, seed: Option<u64>) {
        let s = seed.unwrap_or(42);
        let mut rng = ChaCha8Rng::seed_from_u64(s);
        let n = self.num_oscillators;
        for i in 0..n {
            self.positions[i] = rng.gen_range(-0.5..0.5);
            self.velocities[i] = rng.gen_range(-0.1..0.1);
        }
        self.step_count = 0;
        self.sim_time = 0.0;
    }

    fn get_raw_observable_vector(&self) -> Vec<f64> {
        let mut v = self.positions.clone();
        v.extend_from_slice(&self.velocities);
        v
    }

    fn total_observable_channels(&self) -> usize {
        2 * self.num_oscillators
    }

    fn step_count(&self) -> u64 {
        self.step_count
    }

    fn sim_time(&self) -> f64 {
        self.sim_time
    }
}

