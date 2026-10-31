use sha2::{Digest, Sha256};

#[derive(Debug, Clone, PartialEq)]
pub struct ObservationFrame {
    pub timestamp: f64,
    pub step_index: u64,
    pub readings: Vec<f64>,
    pub frame_hash: String,
}

pub trait SimEnvironment {
    fn step(&mut self, action: Option<&[f64]>);
    fn reset(&mut self, seed: Option<u64>);
    fn get_raw_observable_vector(&self) -> Vec<f64>;
    fn total_observable_channels(&self) -> usize;
    fn step_count(&self) -> u64;
    fn sim_time(&self) -> f64;
}

pub struct ObservationFirewall<E: SimEnvironment> {
    env: E,
    allowed_channels: Vec<usize>,
    max_action_amplitude: f64,
}

impl<E: SimEnvironment> ObservationFirewall<E> {
    pub fn new(env: E, allowed_channels: Vec<usize>, max_action_amplitude: f64) -> Self {
        let total = env.total_observable_channels();
        for &ch in &allowed_channels {
            assert!(ch < total, "Channel index out of bounds: {} >= {}", ch, total);
        }
        Self {
            env,
            allowed_channels,
            max_action_amplitude,
        }
    }

    pub fn observe(&self) -> ObservationFrame {
        let raw = self.env.get_raw_observable_vector();
        let filtered: Vec<f64> = self.allowed_channels.iter().map(|&idx| raw[idx]).collect();

        let mut hasher = Sha256::new();
        hasher.update(format!("{}:{}:", self.env.sim_time(), self.env.step_count()).as_bytes());
        for val in &filtered {
            hasher.update(format!("{:.8e}:", val).as_bytes());
        }
        let frame_hash = format!("{:x}", hasher.finalize());

        ObservationFrame {
            timestamp: self.env.sim_time(),
            step_index: self.env.step_count(),
            readings: filtered,
            frame_hash,
        }
    }

    pub fn probe(&mut self, action: Option<&[f64]>) -> ObservationFrame {
        let clamped: Option<Vec<f64>> = action.map(|act| {
            act.iter()
                .map(|&v| v.clamp(-self.max_action_amplitude, self.max_action_amplitude))
                .collect()
        });

        self.env.step(clamped.as_deref());
        self.observe()
    }

    pub fn reset(&mut self, seed: Option<u64>) -> ObservationFrame {
        self.env.reset(seed);
        self.observe()
    }

    pub fn num_observable_channels(&self) -> usize {
        self.allowed_channels.len()
    }

    pub fn step_count(&self) -> u64 {
        self.env.step_count()
    }

    pub fn sim_time(&self) -> f64 {
        self.env.sim_time()
    }
}

