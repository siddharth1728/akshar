use crate::firewall::SimEnvironment;
use rand::{Rng, SeedableRng};
use rand_chacha::ChaCha8Rng;

pub struct ThermodynamicSwarm {
    num_particles: usize,
    step_size: f64,
    step_count: u64,
    sim_time: f64,
    box_size: f64,
    sigma: f64,
    epsilon: f64,
    damping: f64,
    pos_x: Vec<f64>,
    pos_y: Vec<f64>,
    vel_x: Vec<f64>,
    vel_y: Vec<f64>,
}

impl ThermodynamicSwarm {
    pub fn new(seed: u64, num_particles: usize, step_size: f64) -> Self {
        let mut inst = Self {
            num_particles,
            step_size,
            step_count: 0,
            sim_time: 0.0,
            box_size: 10.0,
            sigma: 1.0,
            epsilon: 0.5,
            damping: 0.1,
            pos_x: Vec::with_capacity(num_particles),
            pos_y: Vec::with_capacity(num_particles),
            vel_x: Vec::with_capacity(num_particles),
            vel_y: Vec::with_capacity(num_particles),
        };
        inst.reset(Some(seed));
        inst
    }
}

impl SimEnvironment for ThermodynamicSwarm {
    fn step(&mut self, action: Option<&[f64]>) {
        let dt = self.step_size;
        let n = self.num_particles;
        let mut fx = vec![0.0; n];
        let mut fy = vec![0.0; n];

        // Pairwise LJ forces
        for i in 0..n {
            for j in (i + 1)..n {
                let dx = self.pos_x[i] - self.pos_x[j];
                let dy = self.pos_y[i] - self.pos_y[j];
                let dist_sq = dx * dx + dy * dy;
                if dist_sq < 16.0 && dist_sq > 0.01 {
                    let dist = dist_sq.sqrt().max(0.2);
                    let r_inv = 1.0 / dist;
                    let sr6 = (self.sigma * r_inv).powi(6);
                    let sr12 = sr6 * sr6;
                    let f_mag = (24.0 * self.epsilon * (2.0 * sr12 - sr6) * (r_inv * r_inv)).clamp(-50.0, 50.0);

                    fx[i] += dx * f_mag;
                    fy[i] += dy * f_mag;
                    fx[j] -= dx * f_mag;
                    fy[j] -= dy * f_mag;
                }
            }
        }

        // Wall forces
        for i in 0..n {
            let px = self.pos_x[i];
            let py = self.pos_y[i];
            if px < 1.0 { fx[i] += 10.0 * (1.0 - px); }
            if self.box_size - px < 1.0 { fx[i] -= 10.0 * (1.0 - (self.box_size - px)); }
            if py < 1.0 { fy[i] += 10.0 * (1.0 - py); }
            if self.box_size - py < 1.0 { fy[i] -= 10.0 * (1.0 - (self.box_size - py)); }

            let mut ax = fx[i] - self.damping * self.vel_x[i];
            let mut ay = fy[i] - self.damping * self.vel_y[i];

            if i == 0 {
                if let Some(act) = action {
                    if act.len() >= 2 {
                        ax += act[0] * 5.0;
                        ay += act[1] * 5.0;
                    }
                }
            }

            self.vel_x[i] += dt * ax;
            self.vel_y[i] += dt * ay;
            self.pos_x[i] += dt * self.vel_x[i];
            self.pos_y[i] += dt * self.vel_y[i];

            // Boundaries
            if self.pos_x[i] < 0.0 {
                self.pos_x[i] = -self.pos_x[i];
                self.vel_x[i] = -0.5 * self.vel_x[i];
            } else if self.pos_x[i] > self.box_size {
                self.pos_x[i] = 2.0 * self.box_size - self.pos_x[i];
                self.vel_x[i] = -0.5 * self.vel_x[i];
            }

            if self.pos_y[i] < 0.0 {
                self.pos_y[i] = -self.pos_y[i];
                self.vel_y[i] = -0.5 * self.vel_y[i];
            } else if self.pos_y[i] > self.box_size {
                self.pos_y[i] = 2.0 * self.box_size - self.pos_y[i];
                self.vel_y[i] = -0.5 * self.vel_y[i];
            }
        }

        self.step_count += 1;
        self.sim_time += dt;
    }

    fn reset(&mut self, seed: Option<u64>) {
        let s = seed.unwrap_or(42);
        let mut rng = ChaCha8Rng::seed_from_u64(s);
        let n = self.num_particles;
        self.pos_x.clear();
        self.pos_y.clear();
        self.vel_x.clear();
        self.vel_y.clear();

        for _ in 0..n {
            self.pos_x.push(rng.gen_range(1.0..(self.box_size - 1.0)));
            self.pos_y.push(rng.gen_range(1.0..(self.box_size - 1.0)));
            self.vel_x.push(rng.gen_range(-0.5..0.5));
            self.vel_y.push(rng.gen_range(-0.5..0.5));
        }
        self.step_count = 0;
        self.sim_time = 0.0;
    }

    fn get_raw_observable_vector(&self) -> Vec<f64> {
        let mut res = Vec::with_capacity(4 * self.num_particles);
        res.extend_from_slice(&self.pos_x);
        res.extend_from_slice(&self.pos_y);
        res.extend_from_slice(&self.vel_x);
        res.extend_from_slice(&self.vel_y);
        res
    }

    fn total_observable_channels(&self) -> usize {
        4 * self.num_particles
    }

    fn step_count(&self) -> u64 {
        self.step_count
    }

    fn sim_time(&self) -> f64 {
        self.sim_time
    }
}

