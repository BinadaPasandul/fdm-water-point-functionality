# Post-hoc development interpretation

Top raw validation permutation features: pumpstrokes, longitude_wp, admin1, latitude_wp, elevation_wp.
Top selected processed features by RF impurity importance: num_indicator__missingindicator_pumpstrokes, num_other__longitude_wp, num_other__latitude_wp, num_other__elevation_wp, cat_unknown__lockedfullday_wp_Unknown.
Importance describes prediction reliance and tree split use, not causality.
Coordinate removal changed CV Macro-F1 by -0.0147, MCC by -0.0186, train-CV gap by -0.0180, and mean country Macro-F1 by -0.0140.
SMOTENC versus its representation control changed Partial recall by +0.1213, Partial precision by -0.1874, Macro-F1 by +0.0156, MCC by +0.0114, and train-CV gap by +0.0176.
The representation control changed Macro-F1 relative to the locked RF by -0.0696; any SMOTENC-versus-locked difference includes that representation change.
Best CV Macro-F1: Locked RF; best MCC: Locked RF; best Partial F1: SMOTENC RF; smallest train-CV gap: RF without coordinates; best mean country Macro-F1: Locked RF.
Coordinate-only ablation is a robustness-oriented candidate under the prespecified screen: no.
Promising overall post-hoc candidate: none.
The Notebook-05 RF remains the official Stage-7 model. Continue with it unless a separate formal reassessment and new external evaluation authorize a change.
