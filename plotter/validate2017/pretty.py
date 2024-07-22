from ROOT import *
from math import *

def plot_ratio(pull,data,mc,xlabel,ylabel,low,high,division):

    Pull = data.Clone("pull")
    Pull.GetXaxis().SetTitle(xlabel)
    Pull.GetYaxis().SetTitleOffset(1.2)
    Pull.GetYaxis().SetTitleSize(0.04)
    Pull.GetYaxis().SetNdivisions(division)
    Pull.GetYaxis().SetLabelSize(0.02)
    #Pull.SetMarkerStyle(20)
    #Pull.SetMarkerSize(0.8)

    if pull:
        print 'Plotting the pulls'
        for i in range(data.GetNbinsX()):
            i += 1
            if data.GetBinContent(i) != 0 :
                Pull.SetBinContent(i,Pull.GetBinContent(i)/Pull.GetBinError(i))
            else: Pull.SetBinContent(i,0)

        Pull.SetMaximum(5.0 )
        Pull.SetMinimum(-5.0)
        Pull.SetFillColor(2)
        Pull.GetYaxis().SetTitle('#sigma(Data-MC)')
        #Pull.Draw("HIST")

    else:
        print 'Plotting the ratio'

        Pull.Divide(mc)
        Pull.SetMaximum(high)
        Pull.SetMinimum(low)
        Pull.GetYaxis().SetTitle(ylabel)
        Pull.SetMarkerColor(1)
        Pull.SetLineColor(1)
        #Pull.Draw("HISTE0")

        ratiosys = data.Clone("ratiosys")
        SetOwnership(ratiosys,False)

        for hbin in range(0,ratiosys.GetNbinsX()+1):
            ratiosys.SetBinContent(hbin+1,1.0)
            if (mc.GetBinContent(hbin+1)>0):
                ratiosys.SetBinError(hbin+1,mc.GetBinError(hbin+1)/mc.GetBinContent(hbin+1))
            else:
                ratiosys.SetBinError(hbin+1,0)
        ratiosys.SetFillColor(kGray) #SetFillColor(ROOT.kYellow)
        ratiosys.SetLineColor(kGray) #SetLineColor(1)                  
        ratiosys.SetLineWidth(1)
        ratiosys.SetMarkerSize(0)        
        #ratiosys.Draw("e2same")
        #Pull.Draw("esame")                  
    return Pull

def plot_cms(preliminary,lumi, c):
    latex2 = TLatex()

    latex2.SetNDC()
    latex2.SetTextSize(0.6*c.GetTopMargin())
    latex2.SetTextFont(42)
    latex2.SetTextAlign(31)
    latex2.DrawLatex(0.9, 0.95,str(lumi) +" fb^{-1} (13.6 TeV)")

    #latex2.SetTextSize(0.035)
    #latex2.SetTextAlign(31) # align right
    #latex2.DrawLatex(0.87, 0.95, str(lumi) +" fb^{-1} (13.6 TeV, 2016)");

    latex3 = TLatex()
    latex3.SetNDC()

    latex3.SetTextSize(0.75*c.GetTopMargin())
    latex3.SetTextFont(62)
    latex3.SetTextAlign(11) # align right
    latex3.DrawLatex(0.22, 0.85, "CMS");
    #latex3.SetTextSize(0.6*c.GetTopMargin()) 
    #latex3.SetTextFont(62)
    #latex3.SetTextAlign(11)
    #latex3.DrawLatex(0.19, 0.85, "CMS")
    latex3.SetTextSize(0.5*c.GetTopMargin())
    latex3.SetTextFont(52)
    latex3.SetTextAlign(11)
    #latex3.SetTextSize(0.5*c.GetTopMargin())
    #latex3.SetTextFont(52)
    #latex3.SetTextAlign(11)    

    if(preliminary):
        latex3.DrawLatex(0.20, 0.8, "Preliminary");
        #latex2.DrawLatex(0.28, 0.85, "Preliminary")
