//! SENSEFORGE: WorldFoundry & Observation Firewall
//! Deterministic procedural simulation engine and information boundary.

pub mod environments;
pub mod firewall;

pub use environments::coupled_oscillators::CoupledOscillators;
pub use environments::reaction_diffusion::ReactionDiffusion;
pub use environments::thermodynamic_swarm::ThermodynamicSwarm;
pub use firewall::{ObservationFirewall, ObservationFrame};

