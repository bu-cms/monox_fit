from utils.generic.logger import initialize_colorized_logger

logger = initialize_colorized_logger(log_level="INFO")


def get_year_from_category(category: str) -> str:
    """Extract the year string from a category name formatted as 'type_year'."""
    _, year = category.split("_")
    allowed_years = {"2017", "2018", "Run3"}
    if year not in allowed_years:
        logger.critical(f"Unrecognized year in category: '{category}' (parsed year: '{year}')", exception_cls=RuntimeError)
    return year


def get_control_region_models(category: str) -> list[str]:
    """Return the list of model names used to define control regions for a given category."""
    if "mono" in category:
        return ["mono_qcd_z", "mono_qcd_w"]
    if "vbf" in category:
        return ["vbf_qcd_z", "vbf_qcd_w", "vbf_ewk_z", "vbf_ewk_w"]
    else:
        logger.critical(f"Could not infer control region definitions for category = {category}.", exception_cls=RuntimeError)
