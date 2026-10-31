use crate::firewall::SimEnvironment;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;

pub struct ReactionDiffusion {
    grid_size: usize,
    step_size: f64,
    step_count: u64,
    sim_time: f64,
    du: f64,
    dv: f64,
    feed_rate: f64,
    kill_rate: f64,
    u: Vec<f64>,
    v: Vec<f64>,
}

impl ReactionDiffusion {
    pub fn new(seed: u64, grid_size: usize, step_size: f64, feed: f64, kill: f64) -> Self {
        let mut inst = Self {
            grid_size,
            step_size,
            step_count: 0,
            sim_time: 0.0,
            du: 0.16,
            dv: 0.08,
            feed_rate: feed,
            kill_rate: kill,
            u: vec![1.0; grid_size],
            v: vec![0.0; grid_size],
        };
        inst.reset(Some(seed));
        inst
    }
}

impl SimEnvironment for ReactionDiffusion {
    fn step(&mut self, action: Option<&[f64]>) {
        let dt = self.step_size * 2.0;
        let n = self.grid_size;
        let mut new_u = self.u.clone();
        let mut new_v = self.v.clone();

        for i in 0..n {
            let left = if i == 0 { n - 1 } else { i - 1 };
            let right = if i == n - 1 { 0 } else { i + 1 };

            let lap_u = self.u[left] + self.u[right] - 2.0 * self.u[i];
            let lap_v = self.v[left] + self.v[right] - 2.0 * self.v[i];

            let uvv = self.u[i] * self.v[i] * self.v[i];
            let du = self.du * lap_u - uvv + self.feed_rate * (1.0 - self.u[i]);
            let mut dv = self.dv * lap_v + uvv - (self.feed_rate + self.kill_rate) * self.v[i];

            if let Some(act) = action {
                if i < act.len() {
                    dv += act[i] * 0.1;
                }
            }

            new_u[i] = (self.u[i] + dt * du).clamp(0.0, 1.0);
            new_v[i] = (self.v[i] + dt * dv).clamp(0.0, 1.0);
        }

        self.u = new_u;
        self.v = new_v;
        self.step_count += 1;
        self.sim_time += self.step_size;
    }

    fn reset(&mut self, seed: Option<u64>) {
        let s = seed.unwrap_or(42);
        let mut rng = ChaCha8Rng::seed_from_u64(s);
        let n = self.grid_size;
        self.u = vec![1.0; n];
        self.v = vec![0.0; n];

        let center = n / 2;
        let radius = (n / 8).max(2);
        for i in (center - radius)..(center + radius) {
            if i < n {
                self.u[i] = 0.5;
                self.v[i] = 0.25;
            }
        }
        for i in 0..n {
            self.v[i] += rng.gen_range(0.0..0.05);
        }
        self.step_count = 0;
        self.sim_time = 0.0;
    }

    fn get_raw_observable_vector(&self) -> Vec<f64> {
        let mut res = self.u.clone();
        res.extend_from_slice(&self.v);
        res
    }

    fn total_observable_channels(&self) -> usize {
        2 * self.grid_size
    }

    fn step_count(&self) -> u64 {
        self.step_count
    }

    fn sim_time(&self) -> f64 {
        self.sim_time
    }
}

