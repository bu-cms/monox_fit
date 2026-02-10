   - `control_samples` has `{label: sample_name}`, taken from `samples_map`
   - `transfer_factors` has `{label: TH1(f"{label}_weights_vbf_2018")}`
   - `CRs` has `{label: Channel(chid = channel_name, catid = f"vbf_2018_{model_name}")}`, `channel_name` taken from `channel_names`
   - veto nuisances: 
        - `veto_2018_(e|m|t)`
        - `f"sys_function_veto_2018_(e|m|t)_cat_vbf_2018_ch_{channel_name}_bin_{b}"`

   - JES/JER: 
        - name in the file: `f"(znunu|wlnu)_over_{jes_region_label}18_(qcd|ewk)_{var}(Up|Down)"` (for all JES/JER variation `var`), `jes_region_label` taken from `jes_region_labels` (inside method)
        - adds to output: `f"{sample}_weights_vbf_2018_{var}_(Up|Down)"`
        - nuisances:  `var`, and  `f"sys_function_{var}_cat_vbf_2018_ch_{channel_name}_bin_{b}"`

   - Theory:
        - spectrums: `f"{spectrum_label}_spectrum_vbf_2018_"`

        - qcd/pdf (`for var in [("mur", "renscale"), ("muf", "facscale"), ("pdf", "pdf")]]`)
            - name in JES/JER file: `f"uncertainty_ratio_{denom_label}_mjj_unc_{ratio}_nlo_{var[0]}_{dir[0]}_2018"`
            - adds to output`f"{region}_weights_vbf_2018_{qcd_label}_{var[1]}_vbf_{dir[1]}"`
            - nuisance: `f"{qcd_label}_{var[1]}_vbf"` and `f"sys_function_{qcd_label}_{var[1]}_vbf_cat_vbf_2018_ch_{channel_name}_bin_{b}"`

        - ewk
            - name in JES/JER file: `f"uncertainty_ratio_{denom_label}_mjj_unc_w_ewkcorr_overz_common_{dir[0]}_2018"`
            - nuisance: `f"{ewk_label}_vbf_bin{b}"` and `f"sys_function_{ewk_label}_vbf_bin{b}_cat_vbf_2018_ch_{channel_name}_bin_{b}"`

   - stat:
    - `f"{label}_weights_vbf_2018_vbf_2018_stat_error_{region}_bin{b-1}_(Up|Down)"`, `region` taken from `region_names`
    - `f"vbf_2018_stat_error_{region}_bin{b-1}"` and `f"sys_function_vbf_2018_stat_error_{region}_bin{b-1}_cat_vbf_2018_ch_{channel_name}_bin_{b}"`

   - Output `Category(category="vbf_2018", catid=f"vbf_2018_{model_name}")`