"""Bounded MRA-JEPA v4 mechanics contracts."""

from .checkpointing import capture_synthetic_checkpoint, restore_synthetic_checkpoint
from .calibration import (
    covariance_calibration,
    gradient_l2_norm,
    variance_floor_calibration,
)
from .contracts import (
    MECHANICS_CONTRACT,
    MICROBATCH_COLLAPSE_TELEMETRY_POLICY,
    VisibilityMasks,
    derive_visibility_masks,
)
from .ema import (
    EMAOptimizerStepController,
    EMATargetEncoder,
    EMAUpdateSummary,
    create_ema_target,
    ema_momentum_at_step,
    ema_target_module,
    update_ema_target,
    validate_momentum,
)
from .gene_tokenizer import GeneExpressionTokenizer
from .losses import frozen_target_copy, jepa_prediction_loss, variance_floor_penalty
from .perceiver_encoder import (
    GeneSetMechanicsEncoder,
    LatentTransformerBlock,
    PerceiverCrossAttention,
    V4AEncoderSkeleton,
)
from .predictor import LatentPredictor
from .pca_summary import FrozenPCA, flatten_slots
from .masking import construct_context_mask, keyed_mask_seed
from .telemetry import (
    EMAParameterHealth,
    EMAUpdateTelemetry,
    RepresentationHealth,
    TargetLatentHealth,
    context_target_agreement,
    ema_parameter_health,
    ema_update_telemetry,
    module_parameter_snapshot,
    online_target_parameter_distance,
    representation_health,
    singular_spectrum_metrics,
    target_latent_health,
)

__all__ = [
    "EMAOptimizerStepController",
    "EMAParameterHealth",
    "EMATargetEncoder",
    "EMAUpdateSummary",
    "EMAUpdateTelemetry",
    "GeneExpressionTokenizer",
    "FrozenPCA",
    "GeneSetMechanicsEncoder",
    "LatentPredictor",
    "LatentTransformerBlock",
    "MECHANICS_CONTRACT",
    "MICROBATCH_COLLAPSE_TELEMETRY_POLICY",
    "PerceiverCrossAttention",
    "RepresentationHealth",
    "TargetLatentHealth",
    "V4AEncoderSkeleton",
    "VisibilityMasks",
    "capture_synthetic_checkpoint",
    "construct_context_mask",
    "context_target_agreement",
    "covariance_calibration",
    "create_ema_target",
    "derive_visibility_masks",
    "ema_parameter_health",
    "ema_momentum_at_step",
    "ema_target_module",
    "ema_update_telemetry",
    "frozen_target_copy",
    "flatten_slots",
    "gradient_l2_norm",
    "jepa_prediction_loss",
    "keyed_mask_seed",
    "module_parameter_snapshot",
    "online_target_parameter_distance",
    "representation_health",
    "restore_synthetic_checkpoint",
    "singular_spectrum_metrics",
    "target_latent_health",
    "update_ema_target",
    "validate_momentum",
    "variance_floor_penalty",
    "variance_floor_calibration",
]
