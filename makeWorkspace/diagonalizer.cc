#ifndef DIAGONALIZER
#define DIAGONALIZER

// ROOT includes
#include "TROOT.h"
#include "TString.h"
#include "TMath.h"
#include "TMatrixDSym.h"
#include "TMatrixD.h"
#include "TVectorD.h"
#include "TIterator.h"
#include "TH2F.h"
#include "TH1F.h"
#include "TH1D.h"

// RooFit includes
#include "RooDataSet.h"
#include "RooRealVar.h"
#include "RooConstVar.h"
#include "RooFormulaVar.h"
#include "RooAddPdf.h"
#include "RooFitResult.h"
#include "RooArgSet.h"
#include "RooArgList.h"
#include "RooCmdArg.h"

// RooStats includes
#include "RooWorkspace.h"

#include "diagonalize.h"

#include <string>
#include <vector>
#include <map>
#include <iostream>

using namespace std;

class diagonalizer {
  
  public:
    diagonalizer(RooWorkspace *wspace);// RooAbsPdf *pdf);

    int generateVariations(RooFitResult *res_ptr);
    void resetPars();  // Reset back to best fit values
    void setEigenset(int,int /*>0 = +1, <0=-1*/);
    void freezeParameters(RooArgSet *args, bool freeze=true);
    void generateWeightedTemplate(TH1F *, RooFormulaVar *, RooRealVar &, RooDataSet *);
    void generateWeightedTemplate(TH1F *histNew, TH1 *pdf_num, std::string wvar, std::string var, RooDataSet *data);
    void generateWeightedDataset(std::string newname, TH1 *pdf_num, std::string wvarname, std::string wvar, RooWorkspace *wspace, std::string dataname);
    TH2F *retCovariance();
    TH2F *retCorrelation();
    
  private:
    RooDataSet *_data_;
    //RooAbsPdf  *_pdf_;
    RooWorkspace *_wspace;

    std::vector<double> original_values;
    RooArgList rooParameters;

    TMatrixD _evec;
    TVectorD _eval;
    TH2F *_h2covar;
    TH2F *_h2corr;
    int _n_par;

    void getArgSetParameters(RooArgList & params,std::vector<double> &val);
    void setArgSetParameters(RooArgList & params,std::vector<double> &val);

    static const bool verb = false;
};

diagonalizer::diagonalizer(RooWorkspace *wspace){//, RooAbsPdf *pdf){
    //_data = data;
    //_pdf = pdf;
    _wspace = wspace;
}


TH2F* diagonalizer::retCovariance(){
  
   if (_h2covar) return _h2covar;
   else { 
	std::cout << "NO COVARIANCE MATRIX, DID YOU DIAGONALIZE YET?" << std::endl;
	return 0;
   }
}
TH2F* diagonalizer::retCorrelation(){
  
   if (_h2corr) return _h2corr;
   else { 
	std::cout << "NO COVARIANCE MATRIX, DID YOU DIAGONALIZE YET?" << std::endl;
	return 0;
   }
}
int diagonalizer::generateVariations(RooFitResult *res_ptr){// std::string dataSetName){
  //RooDataSet *data = (RooDataSet*)_wspace->data(dataSetName.c_str());  // weird but sure
  //assert(data);
  //
  RooArgList rooFloatParameters = res_ptr->floatParsFinal();  // Why not return a set ????!!!
 
  TMatrixD cov  = res_ptr->covarianceMatrix();
  cov.Print();
  //TVectorD eval;
  TMatrixD evec = cov.EigenVectors(_eval);
	
  _n_par = _eval.GetNoElements();
  evec.Print();
  _evec.ResizeTo(_n_par,_n_par);
  _h2covar = new TH2F(Form("covariance_fit_%s",res_ptr->GetName()),"Covariance",_n_par,0,_n_par,_n_par,0,_n_par);
  _h2corr  = new TH2F(Form("correlation_fit_%s",res_ptr->GetName()),"Correlation",_n_par,0,_n_par,_n_par,0,_n_par);
  TMatrixD cor  = res_ptr->correlationMatrix();
  for (int l=0;l<_n_par;l++){
    for (int m=0;m<_n_par;m++){
      _h2covar->SetBinContent(l+1,m+1,cov(l,m));
      _h2corr->SetBinContent(l+1,m+1,cor(l,m));
      _evec(l,m) = evec(l,m); 
    }
  }

  _evec.Print();
  std::cout << "Eigenvalues (squares of errors)"<< std::endl;
  _eval.Print();
  // ---------------------------------------------------------------------------------------------------------------------
  //_evec = evec.Clone();
  //_eval = eval.Clone();

  std::cout << "Number of Parameters from the Fit -- " << _n_par  << std::endl;
  int pcount=1;
  TIterator *parsit = rooFloatParameters.createIterator();
  while (RooAbsArg *arg = (RooAbsArg*)parsit->Next()) {
     RooRealVar *vit = _wspace->var(arg->GetName());
     rooParameters.add(*vit);
     _h2covar->GetXaxis()->SetBinLabel(pcount,vit->GetName());
     _h2covar->GetYaxis()->SetBinLabel(pcount,vit->GetName());
     _h2corr->GetXaxis()->SetBinLabel(pcount,vit->GetName());
     _h2corr->GetYaxis()->SetBinLabel(pcount,vit->GetName());
     pcount++;
  }
  getArgSetParameters(rooParameters,original_values);

  for (int l=0;l<_n_par;l++){
    std::cout << Form("Eigenvector %d = ",l); 
    TIterator *parsit2 = rooParameters.createIterator();
    int m = 0;
    while (RooAbsArg *arg = (RooAbsArg*)parsit2->Next()) {
     RooRealVar *vit = _wspace->var(arg->GetName());
    //for (int m=0;m<_n_par;m++){
     std::cout << Form("%.2f",_evec[m][l]) << "*"<<vit->GetName()<<"+";    
     m++;
    }
    std::cout << std::endl;
  }
  return _n_par;
}
void diagonalizer::resetPars(){
  setArgSetParameters(rooParameters,original_values);
}
void diagonalizer::setEigenset(int par,int direction /*>0 = +1, <0=-1*/){
  //RooArgSet rooParameters;
  //_pdf->getParameters(*x)->Print();

  // fill vector with original parameters
  //std::vector <double> original_values;
  // first set to original parameters
  //setArgSetParameters(rooParameters,original_values);

  std::vector<double> new_values;
  
  int dir = direction>=0 ? 1 : -1;
    
  // this row in evec is the scales for the parameters
  double err = TMath::Sqrt(_eval[par]);
  std::cout << "Setting value of parameters from par " << par << " " << dir << " sigma" << std::endl; 
  new_values.clear(); // make sure its empty before we fill it
  for (int i=0;i<_n_par;i++){
    new_values.push_back(original_values[i] + dir*(_evec[i][par]*err));	
  }

  setArgSetParameters(rooParameters,new_values);

}
void diagonalizer::getArgSetParameters(RooArgList & params,std::vector<double> &val){

  val.clear();
  TIterator* iter(params.createIterator());
  for (TObject *a = iter->Next(); a != 0; a = iter->Next()) {
      RooRealVar *rrv = dynamic_cast<RooRealVar *>(a);
      //std::cout << "RooContainer:: -- Getting values from parameter -- " << std::endl;
      //rrv->Print();
      val.push_back(rrv->getVal());
  }
}

void diagonalizer::setArgSetParameters(RooArgList & params,std::vector<double> &val){

  int i = 0;
  TIterator* iter(params.createIterator());
  for (TObject *a = iter->Next(); a != 0; a = iter->Next()) {
      // each var must be shifted
      RooRealVar *rrv = dynamic_cast<RooRealVar *>(a);
      //std::cout << "RooContainer:: -- Setting values from parameter -- " << std::endl;
      //rrv->Print();
      std::cout << " Set parameter " << rrv->GetName() << " to " << val[i] << std::endl;
      rrv->setVal(val[i]);
      _wspace->var(rrv->GetName())->setVal(val[i]);
      i++;
  }
}
void diagonalizer::freezeParameters(RooArgSet *args, bool freeze){
  TIterator* iter(args->createIterator());
  for (TObject *a = iter->Next(); a != 0; a = iter->Next()) {
      RooRealVar *rrv = dynamic_cast<RooRealVar *>(a);
      rrv->setConstant(freeze);
  }
}
void diagonalizer::generateWeightedTemplate(TH1F *histNew, TH1 *pdf_num, std::string wvar, std::string var, RooDataSet *data){

  // wvar will be the variable to reweight in 
  // var is the variable to be plotted
  histNew->Sumw2();
  int nevents = data->numEntries();
  //const char *varname = var.GetName();
  for (int ev=0;ev<nevents;ev++){
    const RooArgSet *vw = data->get(ev);
    double val    = vw->getRealValue(var.c_str());
    double weight = data->weight();
    //std::cout << val << ", " << weight <<std::endl;
    double wval  = vw->getRealValue(wvar.c_str());
    double cweight = weight;
    if (pdf_num) { 
        //std::cout <<"Zeynep" << wvar<< ", " << wval << ", Weight = "<< cweight << " x " << pdf_num->GetBinContent(pdf_num->FindBin(wval)) << std::endl;
	if (wval >=  pdf_num->GetXaxis()->GetXmin() && wval <  pdf_num->GetXaxis()->GetXmax() ) {
    	  cweight *= pdf_num->GetBinContent(pdf_num->FindBin(wval));
	} else{ 
		if (verb) std::cout << "Event Out of range -> "<< wvar << " = "<< wval << std::endl;
	}
    } else {
    	std::cout <<"Correction function NULL "<<std::endl;
	assert(0);
    }
    histNew->Fill(val,cweight);
  }
  histNew->GetXaxis()->SetTitle(var.c_str());
  histNew = DrawOverflow(histNew);
}

void diagonalizer::generateWeightedTemplate(TH1F *histNew, RooFormulaVar *pdf_num, RooRealVar &var, RooDataSet *data){

  histNew->Sumw2();
  int nevents = data->numEntries();
  const char *varname = var.GetName();
  for (int ev=0;ev<nevents;ev++){
    const RooArgSet *vw = data->get(ev);
    double val    = vw->getRealValue(varname);
    double weight = data->weight();
    //std::cout << val << ", " << weight <<std::endl;
    var.setVal(val);
    double cweight = weight;
    if (pdf_num) { 
    	cweight *= pdf_num->getVal(var);
    } else {
    	std::cout <<"Correction function NULL "<<std::endl;
	assert(0);
    }
    histNew->Fill(val,cweight);
  }
  histNew->GetXaxis()->SetTitle(varname);
}
void diagonalizer::generateWeightedDataset(std::string newname, TH1 *pdf_num, std::string wvarname, std::string wvar, RooWorkspace *wspace, std::string dataname){

  RooDataSet *data =(RooDataSet*) wspace->data(dataname.c_str());
  RooArgSet *args = (RooArgSet*)data->get(0);
  RooRealVar *rwvar = wspace->var(wvarname.c_str());
  RooDataSet datanew(newname.c_str(),newname.c_str(),RooArgSet(*args,*rwvar),wvarname.c_str());

  int nevents = data->numEntries();
  for (int ev=0;ev<nevents;ev++){
    const RooArgSet *vw = data->get(ev);
    double wval    = vw->getRealValue(wvar.c_str());
    double weight = data->weight();
    if (pdf_num) { 
//	std::cout << wval << ", old weight" << weight << std::endl;
	if (wval >=  pdf_num->GetXaxis()->GetXmin() && wval <  pdf_num->GetXaxis()->GetXmax() ) {
    	  weight *= pdf_num->GetBinContent(pdf_num->FindBin(wval));
	} else {

		if (verb) std::cout << "Event Out of range -> "<< wvar << " = "<< wval << std::endl;
	}
//	std::cout << wval << ", new weight" << weight << std::endl;
    } else {
    	std::cout <<"Correction function NULL "<<std::endl;
	assert(0);
    }
    rwvar->setVal(weight);
    datanew.add(*vw,weight);
  }
  wspace->import(datanew);
}

#endif
