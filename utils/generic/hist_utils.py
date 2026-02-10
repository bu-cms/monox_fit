import ROOT as rt  # type: ignore


def histograms_are_equal(h1: rt.TH1, h2: rt.TH1, check_errors: bool = True, tolerance: float = 0.0) -> None:
    """Check if two ROOT histograms have the same binning and content.

    Args:
        h1: First histogram (TH1).
        h2: Second histogram (TH1).
        check_errors: If True, also compare bin errors.
        tolerance: Allowed numerical tolerance for differences (default 0.0 for exact).

    Returns:
        True if histograms are identical within the specified settings, False otherwise.
    """

    if h1.GetNbinsX() != h2.GetNbinsX():
        print(f"Fail: different number of bins ({h1.GetNbinsX()} vs {h2.GetNbinsX()})")
        return False
    if h1.GetXaxis().GetXmin() != h2.GetXaxis().GetXmin():
        print(f"Fail: different x-axis minimum ({h1.GetXaxis().GetXmin()} vs {h2.GetXaxis().GetXmin()})")
        return False
    if h1.GetXaxis().GetXmax() != h2.GetXaxis().GetXmax():
        print(f"Fail: different x-axis maximum ({h1.GetXaxis().GetXmax()} vs {h2.GetXaxis().GetXmax()})")
        return False

    for i in range(1, h1.GetNbinsX() + 2):
        edge1 = h1.GetXaxis().GetBinLowEdge(i)
        edge2 = h2.GetXaxis().GetBinLowEdge(i)
        if abs(edge1 - edge2) > tolerance:
            print(f"Fail: different bin edge at bin {i} ({edge1} vs {edge2})")
            return False

    for i in range(0, h1.GetNbinsX() + 2):
        content1 = h1.GetBinContent(i)
        content2 = h2.GetBinContent(i)
        if abs(content1 - content2) > tolerance:
            print(f"Fail: different bin content at bin {i} ({content1} vs {content2})")
            return False

        if check_errors:
            error1 = h1.GetBinError(i)
            error2 = h2.GetBinError(i)
            if abs(error1 - error2) > tolerance:
                print(f"Fail: different bin error at bin {i} ({error1} vs {error2})")
                return False

    return True
