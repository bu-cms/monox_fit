#ifndef DIAGONALIZE
#define DIAGONALIZE

// ROOT includes
#include "TROOT.h"
#include "TStyle.h"
#include "TCanvas.h"
#include "TPaveText.h"
#include "TLatex.h"
#include "TLegend.h"
#include "TH1F.h"
#include "TF1.h"
#include "TAxis.h"
#include "TTree.h"
#include "TFile.h"
#include "TGraph.h"
#include "TString.h"
#include "TMath.h"
#include "TMatrixDSym.h"
#include "TMatrixD.h"
#include "TVectorD.h"
#include "TIterator.h"

// RooFit includes
#include "RooDataSet.h"
#include "RooRealVar.h"
#include "RooConstVar.h"
#include "RooFormulaVar.h"
#include "RooPlot.h"
#include "RooGenericPdf.h"
#include "RooExponential.h"
#include "RooGaussian.h"
#include "RooBreitWigner.h"
#include "RooVoigtian.h"
#include "RooCBShape.h"
#include "RooChebychev.h"
#include "RooBernstein.h"
#include "RooExtendPdf.h"
#include "RooFFTConvPdf.h"
#include "RooAddPdf.h"
#include "RooFitResult.h"
#include "RooArgSet.h"
#include "RooArgList.h"
#include "RooAddPdf.h"
#include "RooGlobalFunc.h"
#include "RooCmdArg.h"

// RooStats includes
#include "RooWorkspace.h"

#include <string>
#include <vector>
#include <map>
#include <iostream>

using namespace std;
int randC=0;

struct ControlRegion {
  std::string name;
  std::vector<std::pair<std::string, int> > procs;

};

void freezeParameters(RooArgSet *args, bool freeze=1){
  TIterator* iter(args->createIterator());
  for (TObject *a = iter->Next(); a != 0; a = iter->Next()) {
      RooRealVar *rrv = dynamic_cast<RooRealVar *>(a);
      rrv->setConstant(freeze);
  }
}
TH1F *generateTemplate(TH1F *base, TTree *tree, std::string varname, std::string weightname, std::string cut="1>0", std::string ext=""){

  assert(tree);
  assert(base);
  // Correction point to point
  TH1F *histNew = (TH1F*) base->Clone("hnew");
  histNew->Sumw2();
  histNew->SetName(Form("%s%s%d",tree->GetName(),ext.c_str(),randC)); randC++;
  if (weightname!="" ) tree->Draw(Form("%s >> %s",varname.c_str(),histNew->GetName()),Form("%s*(%s)",weightname.c_str(),cut.c_str()));
  else tree->Draw(Form("%s >> %s",varname.c_str(),histNew->GetName()),cut.c_str());
  histNew->GetXaxis()->SetTitle(varname.c_str());
  return histNew;
}

TH1F *generateTemplate(TH1F *base, RooFormulaVar *pdf_num, RooRealVar &var, RooDataSet *data, int dir=1, double weightsf=1., std::string ext="", std::string pvar=""){
  //assert(pdf_num);
  assert(base);
  // Correction point to point
  TH1F *histNew = (TH1F*) base->Clone("hnew");
  histNew->Sumw2();
  if (pdf_num) histNew->SetName(Form("corrected_%s%s",data->GetName(),ext.c_str()));
  else histNew->SetName(Form("%s%s",data->GetName(),ext.c_str()));
  int nevents = data->numEntries();
  const char *varname = var.GetName();
  const char *plotvarname = var.GetName();

  if (pvar!="") plotvarname = pvar.c_str();
  for (int ev=0;ev<nevents;ev++){
    const RooArgSet *vw = data->get(ev);
    double val = vw->getRealValue(varname);
    double pval;
    if (pvar!="") pval = vw->getRealValue(pvar.c_str());
    else pval = vw->getRealValue(varname);

    double weight = data->weight();
    //std::cout << val << ", " << weight <<std::endl;
    var.setVal(val);
    double cweight = weight*weightsf;
    if (pdf_num) { 
      if (dir>=0){
    	cweight *= pdf_num->getVal(var);
	//std::cout << "VAr, pVAr " << var.GetName() << " " << pvar.c_str() << std::endl;
	//std::cout << "DATA " << data->GetName() << ", EVT - " << ev << " VAR " << var.getVal() << " plot VAR " << pval <<", orig = " << weight*weightsf << ", new = " << cweight << " , w corr = " << pdf_num->getVal(var) << std::endl;  
      } else if (dir<0){
    	cweight /= pdf_num->getVal(var);  // Uncorrect!
      } // if ==0, do nothing
    }
    histNew->Fill(pval,cweight);
  }
  histNew->GetXaxis()->SetTitle(plotvarname);
  return histNew;
}

void getArgSetParameters(RooArgList & params,std::vector<double> &val){

  val.clear();
  TIterator* iter(params.createIterator());
  for (TObject *a = iter->Next(); a != 0; a = iter->Next()) {
      RooRealVar *rrv = dynamic_cast<RooRealVar *>(a);
      //std::cout << "RooContainer:: -- Getting values from parameter -- " << std::endl;
      //rrv->Print();
      val.push_back(rrv->getVal());
  }
}

void setArgSetParameters(RooArgList & params,std::vector<double> &val){

  int i = 0;
  TIterator* iter(params.createIterator());
  for (TObject *a = iter->Next(); a != 0; a = iter->Next()) {
      // each var must be shifted
      RooRealVar *rrv = dynamic_cast<RooRealVar *>(a);
      //std::cout << "RooContainer:: -- Setting values from parameter -- " << std::endl;
      //rrv->Print();
      std::cout << " Set parameter " << rrv->GetName() << " to " << val[i] << std::endl;
      rrv->setVal(val[i]);
      i++;
  }
}
double averageTF1Eval(TGraph *f, double x1, double x2){
  
  int np=10;
  double ave = 0;
  double xmax = x1+(x2-x1)/np;
  double step = (x2-x1)/np;
  for (double x=x1;x<=xmax;x+=step){
	ave+=f->Eval(x);
  }
  ave/=np;
  return ave;
}

double calculateWeightedIntegral(RooAbsPdf *pdf, RooRealVar *var, TGraph *cf, double x1, double x2, double step = 0.05){
  // lets assume 0.1 is enough of a step right?????
  double sum = 0;
  for (double x=x1;x<=x2;x+=step){
    var->setVal(x+0.5*step);
    double yval = pdf->getVal(RooArgSet(*var));
    yval *= cf->Eval(x+0.5*step);
    sum+=yval*step;
  }
  return sum;
}

double averageTF1Eval(TH1F *f, double x1){
  
  int b = f->FindBin(x1);
  return f->GetBinContent(b);
}

TH1F *fillHistogramFromPdf(TH1F *base, RooAbsPdf *pdf, RooRealVar *x, TGraph *corrFunc){
  TH1F *newHist = (TH1F*)base->Clone();
  // clear
  for (int b=1;b<=newHist->GetNbinsX();b++){
    newHist->SetBinContent(b,0);
  }
  const RooArgList args(*x);
  double xmin = x->getMin();
  double xmax = x->getMax();
  //pdf->fillHistogram(newHist,args,1.,0,true);
  for (int b=1;b<=base->GetNbinsX();b++){
     double x1 = base->GetBinLowEdge(b);
     double x2 = base->GetBinLowEdge(b+1);
     x->setRange(Form("bin_%d",b),x1,x2);
     double val_i;
     if (corrFunc) {
       val_i = calculateWeightedIntegral(pdf,x,corrFunc,x1,x2);
     } else { 
       RooAbsReal *inte = pdf->createIntegral(RooArgSet(*x),RooArgSet(*x),Form("bin_%d",b));
       val_i = inte->getVal();
     }
     //if (corrFunc) val_i*=averageTF1Eval(corrFunc,x1,x2);
     newHist->SetBinContent(b,val_i);
     newHist->SetBinError(b,0);
  }
  x->setRange(xmin,xmax);
  return newHist;
}

TH1F *DrawOverflow(TH1F* h){

    UInt_t nx    = h->GetNbinsX();
    float error = sqrt(h->GetBinError(nx)*h->GetBinError(nx) +  h->GetBinError(nx+1)*h->GetBinError(nx+1));
    h->SetBinContent(nx,h->GetBinContent(nx)+h->GetBinContent(nx+1));
    h->SetBinContent(nx+1,0);
    h->SetBinError(nx,error);
    h->SetBinError(nx+1,0);
    //h->SetEntries(h->GetEffectiveEntries());

    /*
    //function to paint the histogram h with an extra bin for overflows
    UInt_t nx    = h->GetNbinsX()+1;
    Double_t *xbins= new Double_t[nx+1];
    for (UInt_t i=0;i<nx;i++)
        xbins[i]=h->GetBinLowEdge(i+1);
    xbins[nx]=xbins[nx-1]+h->GetBinWidth(nx);
    //book a temporary histogram having extra bins for overflows
    TH1F *htmp = new TH1F(h->GetName(), h->GetTitle(), nx, xbins);
    htmp->Sumw2();
    //fill the new histogram including the overflows
    for (UInt_t i=1; i<=nx; i++) {
        htmp->SetBinContent(htmp->FindBin(htmp->GetBinCenter(i)),h->GetBinContent(i));
        htmp->SetBinError(htmp->FindBin(htmp->GetBinCenter(i)),h->GetBinError(i));
    }
    htmp->SetBinContent(htmp->FindBin(h->GetBinLowEdge(1)-1), h->GetBinContent(0));
    htmp->SetBinError(htmp->FindBin(h->GetBinLowEdge(1)-1), h->GetBinError(0));
    // Restore the number of entries
    htmp->SetEntries(h->GetEffectiveEntries());
    return htmp;
    */
    return h;
}

TH1F *fillHistogramFromPdf(TH1F *base, RooAbsPdf *pdf, RooRealVar *x, TH1F *corrFunc){
  TH1F *newHist = (TH1F*)base->Clone();
  // clear
  for (int b=1;b<=newHist->GetNbinsX();b++){
    newHist->SetBinContent(b,0);
  }
  const RooArgList args(*x);
  double xmin = x->getMin();
  double xmax = x->getMax();
  //pdf->fillHistogram(newHist,args,1.,0,true);
  for (int b=1;b<=base->GetNbinsX();b++){
     double x1 = base->GetBinLowEdge(b);
     double x2 = base->GetBinLowEdge(b+1);
     x->setRange(Form("bin_%d",b),x1,x2);
     double val_i=0.;
     if (corrFunc) {
       //val_i = calculateWeightedIntegral(pdf,x,corrFunc,x1,x2);
       RooAbsReal *inte = pdf->createIntegral(RooArgSet(*x),RooArgSet(*x),Form("bin_%d",b));
       val_i = inte->getVal(*x)*(corrFunc->GetBinContent(corrFunc->FindBin((x1+x2)/2)));
       std::cout << " range = " << x1 << "->" << x2 << "Correction = " << corrFunc->GetBinContent(corrFunc->FindBin((x1+x2)/2)) << std::endl;
     } else { 
       RooAbsReal *inte = pdf->createIntegral(RooArgSet(*x),RooArgSet(*x),Form("bin_%d",b));
       val_i = inte->getVal(*x);
     }
     //if (corrFunc) val_i*=averageTF1Eval(corrFunc,x1,x2);
     newHist->SetBinContent(b,val_i);
     newHist->SetBinError(b,0);
  }
  x->setRange(xmin,xmax);
  return newHist;
}

void generateVariations(TH1F *base_hist,RooFitResult *res_ptr, RooAbsPdf *pdf_ptr, RooRealVar *x,std::vector<TH1F> & v_th1f_,RooWorkspace *wspace, TH1F *corrFunc, TDirectory *fout=0){

// Generate variations from a simple getHistogram from a Pdf. There can also be a correction applied ON top of this pdf st the integral is weigted by the average of the 
// correction in that (needs a little work but should be ok) 
  TMatrixD cov = res_ptr->covarianceMatrix();
  TVectorD eval;
  TMatrixD evec   = cov.EigenVectors(eval);
  evec.Print();
  std::cout << "Eigenvalues (squares of errors)"<< std::endl;
  eval.Print();
  // ---------------------------------------------------------------------------------------------------------------------
  double norm = base_hist->Integral();

  // now we know that the eigenvalues of the covariance matrix must scale each parameter as given by the new paraemeters
  int n_par = eval.GetNoElements();
  std::cout << "Number of Parameters from the Fit -- " << n_par  << std::endl;
  RooArgList rooFloatParameters = res_ptr->floatParsFinal();  // Why not return a set ????!!!
  // Sigh 
  RooArgList rooParameters;
  TIterator *parsit = rooFloatParameters.createIterator();
  while (RooAbsArg *arg = (RooAbsArg*)parsit->Next()) {
     RooRealVar *vit = wspace->var(arg->GetName());
     rooParameters.add(*vit);
  }

  //RooArgSet rooParameters;
  //TIterator *parsit = rooParameterList->createIterator
  pdf_ptr->getParameters(*x)->Print();

  // fill vector with original parameters
  std::vector <double> original_values;
  getArgSetParameters(rooParameters,original_values);

  TH1F * temp_hist;

  // now loop over columns of the eigenvector Matrix
  std::vector<double> new_values;
  for (int par=0;par<n_par;par++){
    
    // this row in evec is the scales for the parameters
    double err = TMath::Sqrt(eval[par]);

    new_values.clear(); // make sure its empty before we fill it
    for (int i=0;i<n_par;i++){
      new_values.push_back(original_values[i] + evec[i][par]*err);	
    }

    std::cout << "Systematic from parameter "<< par << " +1 sigma" << std::endl;
    setArgSetParameters(rooParameters,new_values);

    temp_hist = (TH1F*) fillHistogramFromPdf(base_hist,pdf_ptr,x,corrFunc);
    //temp_hist->Scale(norm/temp_hist->Integral());
    temp_hist->SetName(Form("%s_%s_param%dUp",pdf_ptr->GetName(),res_ptr->GetName(),par));
    v_th1f_.push_back(*temp_hist);

    // now -1 sigma
    new_values.clear();  // need to clear again
    for (int i=0;i<n_par;i++){
        new_values.push_back(original_values[i] - evec[i][par]*err);	
    }

    std::cout << "Systematic from parameter "<< par << " -1 sigma" << std::endl;
    setArgSetParameters(rooParameters,new_values);

    temp_hist = (TH1F*) fillHistogramFromPdf(base_hist,pdf_ptr,x,corrFunc);
    //temp_hist->Scale(norm/temp_hist->Integral());
    temp_hist->SetName(Form("%s_%s_param%dDown",pdf_ptr->GetName(),res_ptr->GetName(),par));
    v_th1f_.push_back(*temp_hist);
 
    // after each parameter we reset the originals back
    std::cout << "Reset to Original Values " << std::endl;
    setArgSetParameters(rooParameters,original_values);
  } 
  std::cout << "Generated systematic varitions from " << res_ptr->GetName()<<std::endl;   

  /*
  if (fout){
   //double norm = base_hist->Integral();
   int colit=2, styleit=1;
   TCanvas *can_systs = new TCanvas("can_systs","can_systs",800,600);
   TLegend *leg = new TLegend(0.6,0.4,0.89,0.89); leg->SetFillColor(0); leg->SetTextFont(42);
   base_hist->SetLineColor(1);base_hist->SetLineWidth(3); base_hist->Draw();
   for (std::vector<TH1F>::iterator hit=v_th1f_.begin();hit!=v_th1f_.end();hit++){
     hit->SetLineColor(colit);
     hit->SetLineWidth(3);
     hit->SetLineStyle(styleit%2+1);
     leg->AddEntry(&(*hit),hit->GetName(),"L");
     //hit->Scale(norm/hit->Integral());
     std::cout << "Saved Systematic " << hit->GetName()<< std::endl;
     hit->Draw("same"); 
     //hit->Write();
     styleit++;
     if (styleit%2==1) colit++;
   }
   leg->Draw();
   fout->WriteTObject(can_systs);
  }
   */
}

void generateVariations(TH1F *base_hist,RooFitResult *res_ptr, RooFormulaVar *pdf_ptr, RooRealVar *x,std::vector<TH1F> & v_th1f_,RooWorkspace *wspace, std::string dataSetName, TDirectory *fout=0){
// Generate variations for a CORRECTION to a dataset  
  RooDataSet *data = (RooDataSet*)wspace->data(dataSetName.c_str());
  assert(data);
  // The "Pdf" will be a correction function and we will correct the Z->nunu/W->lnu histograms with it
  //


  double norm = base_hist->Integral();
 
  TMatrixD cov = res_ptr->covarianceMatrix();
  TVectorD eval;
  TMatrixD evec   = cov.EigenVectors(eval);
  evec.Print();
  std::cout << "Eigenvalues (squares of errors)"<< std::endl;
  eval.Print();
  // ---------------------------------------------------------------------------------------------------------------------

  // now we know that the eigenvalues of the covariance matrix must scale each parameter as given by the new paraemeters
  int n_par = eval.GetNoElements();
  std::cout << "Number of Parameters from the Fit -- " << n_par  << std::endl;
  RooArgList rooFloatParameters = res_ptr->floatParsFinal();  // Why not return a set ????!!!
  // Sigh 
  RooArgList rooParameters;
  TIterator *parsit = rooFloatParameters.createIterator();
  while (RooAbsArg *arg = (RooAbsArg*)parsit->Next()) {
     RooRealVar *vit = wspace->var(arg->GetName());
     rooParameters.add(*vit);
  }

  //RooArgSet rooParameters;
  //TIterator *parsit = rooParameterList->createIterator
  pdf_ptr->getParameters(*x)->Print();

  // fill vector with original parameters
  std::vector <double> original_values;
  getArgSetParameters(rooParameters,original_values);

  TH1F * temp_hist;

  // now loop over columns of the eigenvector Matrix
  std::vector<double> new_values;
  for (int par=0;par<n_par;par++){
    
    // this row in evec is the scales for the parameters

    double err = TMath::Sqrt(eval[par]);

    new_values.clear(); // make sure its empty before we fill it
    for (int i=0;i<n_par;i++){
      new_values.push_back(original_values[i] + evec[i][par]*err);	
    }

    std::cout << "Systematic from parameter "<< par << " +1 sigma" << std::endl;
    setArgSetParameters(rooParameters,new_values);

    temp_hist = (TH1F*) generateTemplate(base_hist,pdf_ptr,*x,data);
    temp_hist->SetName(Form("%s_%s_param%dUp",dataSetName.c_str(),res_ptr->GetName(),par));
    //temp_hist->Scale(norm/temp_hist->Integral());
    v_th1f_.push_back(*temp_hist);

    // now -1 sigma
    new_values.clear();  // need to clear again
    for (int i=0;i<n_par;i++){
        new_values.push_back(original_values[i] - evec[i][par]*err);	
    }

    std::cout << "Systematic from parameter "<< par << " -1 sigma" << std::endl;
    setArgSetParameters(rooParameters,new_values);

    temp_hist = (TH1F*) generateTemplate(base_hist,pdf_ptr,*x,data);
    temp_hist->SetName(Form("%s_%s_param%dDown",dataSetName.c_str(),res_ptr->GetName(),par));
    //temp_hist->Scale(norm/temp_hist->Integral());
    v_th1f_.push_back(*temp_hist);
 
    // after each parameter we reset the originals back
    std::cout << "Reset to Original Values " << std::endl;
    setArgSetParameters(rooParameters,original_values);
  } 
  std::cout << "Generated systematic varitions from " << res_ptr->GetName()<<std::endl;   

  /*
  if (fout){ 
   fout->cd();
   int colit=2, styleit=1;
   TCanvas *can_systs = new TCanvas("can_systs","can_systs",800,600);
   TLegend *leg = new TLegend(0.6,0.4,0.89,0.89); leg->SetFillColor(0); leg->SetTextFont(42);
   base_hist->SetLineColor(1);base_hist->SetLineWidth(3); base_hist->Draw();
   for (std::vector<TH1F>::iterator hit=v_th1f_.begin();hit!=v_th1f_.end();hit++){
     hit->SetLineColor(colit);
     hit->SetLineWidth(3);
     hit->SetLineStyle(styleit%2+1);
     leg->AddEntry(&(*hit),hit->GetName(),"L");
    // hit->Scale(norm/hit->Integral());
     hit->Draw("same"); 
     std::cout << "Saved Systematic " << hit->GetName()<< std::endl;
     //hit->Write();
     styleit++;
     if (styleit%2==1) colit++;
   }
   leg->Draw();
   fout->WriteTObject(can_systs);
  }
  */
}

#endif
