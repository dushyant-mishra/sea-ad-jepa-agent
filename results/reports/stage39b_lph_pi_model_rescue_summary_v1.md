# Stage 39B-LPH PI model rescue summary

## Short answer

LPH training allowed: `True`. LPH training ran: `True`.

| best_lph_model_id | best_lph_condition | stage27c_reference_mean | best_lph_mean | delta_vs_stage27c | best_lph_minus_module_mean_baseline | target_drop_gate_pass | beats_no_lph_matched_baseline | beats_shuffled_latent_target_control | internal_performance_pass | graph_specific_pass | recommended_next_step | allowed_claim_language | prohibited_claim_language |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lph_aux_head_shuffled_latent_target | lph_aux_head_shuffled_latent_target | 0.3267024400121495 | 0.32559684114609705 | -0.0011055988660524374 | 0.012796841146097027 | False | False | False | False | False | do not reprioritize candidates; return to metadata/external support or redesign LPH | internal model-improvement experiment; latent prediction auxiliary head; representation-space prediction; hypothesis prioritization only | generative decoder; synthetic biological data; clean external validation; validated mechanism; causal regulator; therapeutic target; disease-modifying target; gene-ablation result |

## Controls

| comparison | left_condition | right_condition | delta | passes |
| --- | --- | --- | --- | --- |
| real_lph_vs_no_lph_matched_baseline | lph_aux_head_real | no_lph_matched_baseline | 0.009982788296041267 | True |
| real_lph_vs_shuffled_latent_target | lph_aux_head_real | lph_aux_head_shuffled_latent_target | -0.028206945428774 | False |
| real_lph_vs_shuffled_context | lph_aux_head_real | lph_aux_head_shuffled_context | 0.02746177989267995 | True |
| real_lph_vs_no_graph_identity | lph_aux_head_real | lph_aux_head_no_graph_or_identity | 0.0 | True |

## Target-level results

| condition | target | n_donors | pooled_oof_spearman | mse | prediction_variance | mean_pooled_oof_spearman |
| --- | --- | --- | --- | --- | --- | --- |
| lph_aux_head_no_graph_or_identity | 6e10/A_beta | 84 | 0.3419864331274679 | 7.672293712778322 | 0.8030669787970317 | 0.29738989571732305 |
| lph_aux_head_no_graph_or_identity | AT8 | 84 | 0.531294927609598 | 1.16407426748272 | 0.6208011942361842 | 0.29738989571732305 |
| lph_aux_head_no_graph_or_identity | GFAP | 84 | 0.3306267085147312 | 20.31688508980963 | 2.0689022585941976 | 0.29738989571732305 |
| lph_aux_head_no_graph_or_identity | Iba1 | 84 | -0.04683608383112281 | 5.686740507082075 | 0.5969658957521425 | 0.29738989571732305 |
| lph_aux_head_no_graph_or_identity | NeuN | 84 | 0.32987749316594106 | 3.3569500624584765 | 0.5384291307569513 | 0.29738989571732305 |
| lph_aux_head_real | 6e10/A_beta | 84 | 0.3419864331274679 | 7.672293712778322 | 0.8030669787970317 | 0.29738989571732305 |
| lph_aux_head_real | AT8 | 84 | 0.531294927609598 | 1.16407426748272 | 0.6208011942361842 | 0.29738989571732305 |
| lph_aux_head_real | GFAP | 84 | 0.3306267085147312 | 20.31688508980963 | 2.0689022585941976 | 0.29738989571732305 |
| lph_aux_head_real | Iba1 | 84 | -0.04683608383112281 | 5.686740507082075 | 0.5969658957521425 | 0.29738989571732305 |
| lph_aux_head_real | NeuN | 84 | 0.32987749316594106 | 3.3569500624584765 | 0.5384291307569513 | 0.29738989571732305 |
| lph_aux_head_shuffled_context | 6e10/A_beta | 84 | 0.31961121798116837 | 8.219969815205017 | 0.519063738517557 | 0.2699281158246431 |
| lph_aux_head_shuffled_context | AT8 | 84 | 0.4547332185886403 | 1.3739752470913331 | 0.588138890696105 | 0.2699281158246431 |
| lph_aux_head_shuffled_context | GFAP | 84 | 0.23677229928115825 | 22.133515710047554 | 1.8401454337656973 | 0.2699281158246431 |
| lph_aux_head_shuffled_context | Iba1 | 84 | -0.1424926597144882 | 5.814174257086566 | 0.5928597086349231 | 0.2699281158246431 |
| lph_aux_head_shuffled_context | NeuN | 84 | 0.48101650298673687 | 3.104208822678377 | 0.7576440942809819 | 0.2699281158246431 |
| lph_aux_head_shuffled_latent_target | 6e10/A_beta | 84 | 0.42678951098511697 | 7.676969616583097 | 0.45781821884572754 | 0.32559684114609705 |
| lph_aux_head_shuffled_latent_target | AT8 | 84 | 0.4576085856029159 | 1.2273282002934311 | 0.6651292653103299 | 0.32559684114609705 |
| lph_aux_head_shuffled_latent_target | GFAP | 84 | 0.35132125139212317 | 19.878672548302834 | 2.582461358135465 | 0.32559684114609705 |
| lph_aux_head_shuffled_latent_target | Iba1 | 84 | -0.062103877695656576 | 5.182303987582616 | 0.3897909082563974 | 0.32559684114609705 |
| lph_aux_head_shuffled_latent_target | NeuN | 84 | 0.4543687354459856 | 3.174660631851049 | 0.552822820395186 | 0.32559684114609705 |
| no_lph_matched_baseline | 6e10/A_beta | 84 | 0.35271843677229936 | 8.196339484767268 | 0.27452980785598446 | 0.2874071074212818 |
| no_lph_matched_baseline | AT8 | 84 | 0.5359724612736662 | 1.1862188141702052 | 1.6707753518635498 | 0.2874071074212818 |
| no_lph_matched_baseline | GFAP | 84 | 0.21368836691303028 | 22.783517803576803 | 0.7695924806729588 | 0.2874071074212818 |
| no_lph_matched_baseline | Iba1 | 84 | -0.1207856636630556 | 5.090071709679429 | 0.1410808377233948 | 0.2874071074212818 |
| no_lph_matched_baseline | NeuN | 84 | 0.45544193581046877 | 3.3395926975920505 | 1.421984432690171 | 0.2874071074212818 |

## Interpretation

This is an internal benchmark experiment only. Candidates should not be reprioritized unless the LPH condition beats Stage 27C and the matched/shuffled controls under the predeclared gates. No clean external validation, causal, therapeutic, disease-modifying, or gene-ablation claim is supported.
